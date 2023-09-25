"""
This module is used to monitor alarms from OPC UA servers.
It reads multiple OPC UA server config files and starts a subscription to each server.
If the send_sms flag is set to True, it will send an SMS message to the specified phone number else it will log the message.

It has been tested and works with a Siemens PLC.

version: 1.0.0 Inital commit by Roberts balulis
"""
__version__ = "1.0.0"

import asyncio
from datetime import datetime

from asyncua import ua, Client

try:
    from create_logger import setup_logger
    from opcua_client import connect_opcua
    from data_encrypt import DataEncryptor
    from config_handler import ConfigHandler
except ImportError:
    print(f"Some modules was not found in. Please make sure it is in the same directory as this script.")

try:
    from sms_sender import send_sms
except ImportError:
    print(f"The sms_sender module was not found. You will not be able to send SMS messages.")

####################################

# Logging
logger_programming = setup_logger('opcua_prog_alarm')
logger_opcua_alarm = setup_logger("opcua_alarms")

# Config files that does not contain sensitive data
config_manager = ConfigHandler()
phone_book = config_manager.phone_book
opcua_alarm_config = config_manager.opcua_server_alarm_config

# Config files that contains sensitive data
opcua_server_config_path = "opcua_server_config.json"

# Environment variables
OPCUA_SERVER_WINDOWS_ENV_KEY_NAME = "opcua_key"

# Config data
SEND_SMS:bool = opcua_alarm_config["send_sms"]
ALARM_CONDITION_TYPE:str = opcua_alarm_config["alarm_condition_type"]
SERVER_NODE_IDENTIFIER:int = opcua_alarm_config["server_node_identifier"]
SERVER_NODE_NAMESPACE_INDEX:int = opcua_alarm_config["server_node_namespace_index"]

# Från engelska square eagle per donut till svenska
DAY_TRANSLATION = {
            'Monday': 'Måndag',
            'Tuesday': 'Tisdag',
            'Wednesday': 'Onsdag',
            'Thursday': 'Torsdag',
            'Friday': 'Fredag',
            'Saturday': 'Lördag',
            'Sunday': 'Söndag'
            }

####################################


async def subscribe_to_server(adresses: str, username: str, password: str):
    """
    Parameters
    ----------
    adresses - The address of the OPC UA server
    username - The username to use when connecting to the OPC UA server
    password - The password to use when connecting to the OPC UA server
    """
    client:Client = None
    subscription_active = False

    while True:
        try:
            if client is None:
                client = await connect_opcua(adresses, username, password)

            await client.check_connection()

            if not subscription_active:
                handler = SubHandler(adresses)
                sub = await client.create_subscription(1000, handler)
                alarmConditionType = client.get_node("ns=0;i=2915")
                server_node = client.get_node(ua.NodeId(Identifier=2253,
                                                        NodeIdType=ua.NodeIdType.Numeric, NamespaceIndex=0))
                subscription_active = True

            await sub.subscribe_alarms_and_conditions(server_node,alarmConditionType)

            while True:
                await asyncio.sleep(1)
                await client.check_connection()

        except (ConnectionError, ua.UaError):
            logger_programming.warning("Reconnecting in 10 seconds")
            await asyncio.sleep(10)

        except Exception as e:
            logger_programming.error(f"Error connecting or subscribing to server {adresses}: {e}")
            client = None
            subscription_active = False
            await asyncio.sleep(10)


class SubHandler:
    """
    Handles the events received from the OPC UA server, and what to do with them.
    """

    def __init__(self, address: str):
        self.address = address

    def status_change_notification(self, status: ua.StatusChangeNotification):
        """
        Called when a status change notification is received from the server.
        """

        logger_opcua_alarm(f"Status change received from subscription with status: {status}")


    async def event_notification(self, event):
        """
        This function is called when an event is received from the OPC UA server.
        and saves it to a log file.
        returns: the event message
        """

        opcua_alarm_message = {
            "New event received from": self.address
        }

        attributes_to_check = [
            "Message", "Time", "Severity", "SuppressedOrShelved",
            "AckedState", "ConditionClassId", "NodeId", "Quality", "Retain",
            "ActiveState", "EnabledState"
        ]

        for attribute in attributes_to_check:
            if hasattr(event, attribute):
                value = getattr(event, attribute)
                if hasattr(value, "Text"):
                    value = value.Text
                opcua_alarm_message[attribute] = value

        if hasattr(event, "NodeId") and hasattr(event.NodeId, "Identifier"):
            opcua_alarm_message["Identifier"] = str(event.NodeId.Identifier)

        if SEND_SMS:
            if opcua_alarm_message["ActiveState"] == "Active":
                await self.user_notification(opcua_alarm_message["Message"], opcua_alarm_message['Severity'])
                logger_opcua_alarm.info(f"New event received from {self.address}: {opcua_alarm_message}")


    async def user_notification(self, opcua_alarm_message:str, severity:int):

        current_time = datetime.now().time()

        current_day = DAY_TRANSLATION[datetime.now().strftime('%A')]

        for user in phone_book:
            if user.get('Active') == 'Yes':
                time_settings = user.get('timeSettings', [])

                for setting in time_settings:
                    if current_day in setting.get('days', []):
                        start_time = datetime.strptime(setting.get('startTime', '00:00'), '%H:%M').time()
                        end_time = datetime.strptime(setting.get('endTime', '00:00'), '%H:%M').time()

                        if start_time <= current_time <= end_time:
                            lowest_severity = setting.get('lowestSeverity')
                            highest_severity = setting.get('highestSeverity')
                            lowest_severity = int(lowest_severity)
                            highest_severity = int(highest_severity)

                            if lowest_severity <= severity <= highest_severity:
                                phone_number = user.get('phone_number')
                                name = user.get('Name')
                                message = f"Medelande från pumpstation: {opcua_alarm_message}, allvarlighetsgrad: {severity}"
                                #send_sms(phone_number, message)
                                logger_opcua_alarm.info(f"Sent SMS to {name} at {phone_number}")
                                print(f"Sent SMS to {name} at {phone_number}")


async def monitor_alarms():
    """
    Reads the OPC UA server config file and starts a subscription to each server.
    """

    data_encrypt = DataEncryptor()
    opcua_config = data_encrypt.encrypt_credentials(opcua_server_config_path, OPCUA_SERVER_WINDOWS_ENV_KEY_NAME)

    if opcua_config is None:
        logger_programming.error("Could not read OPC UA config file")
        raise FileNotFoundError("Could not read OPC UA config file")

    tasks = []

    for server in opcua_config["servers"]:
        encrypted_username = server["username"]
        encrypted_password = server["password"]
        encrypted_address = server["address"]

        tasks.append(asyncio.create_task(subscribe_to_server(encrypted_address,
                                                            encrypted_username, encrypted_password)))

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(monitor_alarms())
