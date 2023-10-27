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
import logging
import concurrent.futures

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

# Config files
config_manager = ConfigHandler()
phone_book = config_manager.phone_book
opcua_alarm_config = config_manager.opcua_server_alarm_config

# Config data
SEND_SMS:bool = opcua_alarm_config["config"]["send_sms"]
ALARM_CONDITION_TYPE:str = opcua_alarm_config["config"]["alarm_condition_type"]
SERVER_NODE_IDENTIFIER:int = opcua_alarm_config["config"]["server_node_identifier"]
SERVER_NODE_NAMESPACE_INDEX:int = opcua_alarm_config["config"]["server_node_namespace_index"]
DAY_TRANSLATION:dict = opcua_alarm_config["day_translation"]
OPCUA_SERVER_CRED_PATH:str = opcua_alarm_config["opcua_server_cred_path"]
OPCUA_SERVER_WINDOWS_ENV_KEY_NAME:str = opcua_alarm_config["environment_variables"]["opcua"]
SMS_MESSAGE:str = opcua_alarm_config["config"]["messege"]
####################################


async def subscribe_to_server(adresses: str, username: str, password: str):
    """
    Parameters
    ----------
    adresses - The address of the OPC UA server
    username - The username to use when connecting to the OPC UA server
    password - The password to use when connecting to the OPC UA server
    """

    retry_delay = 5  # Initial retry delay
    max_retry_delay = 60  # Maximum retry delay
    client = None
    sub = None

    while True:
        try:
            if not client:
                client = await connect_opcua(adresses, username, password)

            async with client as client_instance:
                await client_instance.check_connection()
                conditionType = await client_instance.get_node("ns=0;i=2782")
                alarmConditionType = await client_instance.get_node("ns=0;i=2915")

                msclt = SubHandler(adresses)
                sub = await client_instance.create_subscription(0, msclt)
                handle = await sub.subscribe_alarms_and_conditions(client_instance.nodes.server, alarmConditionType)
                await conditionType.call_method("0:ConditionRefresh", ua.Variant(sub.subscription_id, ua.VariantType.UInt32))

                logger_programming.info("Made a new subscription")
                retry_delay = 5  # Reset the retry delay upon successful connection

                while True:
                    await asyncio.sleep(0.1)
                    await client_instance.check_connection()

        except (ConnectionError, ua.UaError) as e:
            logger_programming.warning(f"{e} Reconnecting in {retry_delay} seconds")
            if client and sub:
                await client.delete_subscriptions(sub)
                await client.disconnect()
                client = None
            if client:
                await client.disconnect()
                client = None

            await asyncio.sleep(retry_delay)
            retry_delay = min(max_retry_delay, retry_delay * 2)  # Increment the delay, but cap it

        except Exception as e:
            logger_programming.error(f"Error connecting or subscribing to server {adresses}: {e}")
            if client and sub:
                await client.delete_subscriptions(sub)
                await client.disconnect()
                client = None
            if client:
                await client.disconnect()
                client = None

            await asyncio.sleep(retry_delay)
            retry_delay = min(max_retry_delay, retry_delay * 2)  # Increment the delay, but cap it


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
        # Handle the status change event. This could be logging the change, raising an alert, etc.
        print(f"Status change received from subscription with status: {status}")
        logger_opcua_alarm.info(status)



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

        else:
            if opcua_alarm_message["ActiveState"] == "Active":
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
                                message = f"{SMS_MESSAGE} {opcua_alarm_message}, allvarlighetsgrad: {severity}"
                                print("Trying to send a sms")
                                loop = asyncio.get_running_loop()
                                with concurrent.futures.ThreadPoolExecutor() as pool:
                                    result = await loop.run_in_executor(pool, send_sms, phone_number, message)
                                logger_opcua_alarm.info(f"Sent SMS to {name} at {phone_number}")
                                print(f"Sent SMS to {name} at {phone_number}")


async def monitor_alarms():
    """
    Reads the OPC UA server config file and starts a subscription to each server.
    """

    data_encrypt = DataEncryptor()
    opcua_config = data_encrypt.encrypt_credentials(OPCUA_SERVER_CRED_PATH, OPCUA_SERVER_WINDOWS_ENV_KEY_NAME)

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
