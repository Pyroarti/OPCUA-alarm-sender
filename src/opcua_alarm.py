import asyncio
from asyncua import ua, Server, Client
import asyncua.common.subscription
from create_logger import setup_logger
from opcua_client import connect_opcua
import traceback
import os
import json

from sms_sender import send_sms

logger_alarm = setup_logger('opcua_prog_alarm')
logger_opcua_alarm = setup_logger("opcua_alarms")

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
config_dir = os.path.join(parent_dir, "configs")
phone_book_file = os.path.join(config_dir, 'phone_book.json')


async def subscribe_to_server(adresses, username, password):
    """
    This function handles the process of connecting and subscribing to the OPCUA server.
    Args:
        adresses (str): Address of the OPCUA server.
        username (str): Encrypted username for the OPCUA server.
        password (str): Encrypted password for the OPCUA server.
    """

    client: Client = None

    while True:
        try:
            if client is None:
                client:Client = await connect_opcua(adresses, username, password)

            else:

                try:
                    handler = SubHandler(adresses)
                    sub = await client.create_subscription(1000, handler)
                    alarmConditionType = client.get_node("ns=0;i=2915")

                    server_node = client.get_node(ua.NodeId(Identifier=2253,
                                                            NodeIdType=ua.NodeIdType.Numeric,
                                                            NamespaceIndex=0))

                    await sub.subscribe_alarms_and_conditions(server_node, alarmConditionType)
                    break
                except Exception as e:
                    logger_alarm.error(f"Error subscribing to server {adresses}: {e}")
                    await asyncio.sleep(10)
                    continue

        except Exception as e:
            logger_alarm.error(f"Error connecting to server {adresses}: {e}")
            await asyncio.sleep(10)
            continue


class SubHandler(object):
    """
    Subscription Handler class that receives the events from the OPC UA server.
    """


    async def __init__(self, address, phone_book_file):
        self.address = address
        self.phone_book_file = phone_book_file

    async def event_notification(self, event):

        try:
            message = str(event.Message.Text)
            date = event.Time
            active_state_id = None
            severity = event.Severity
            enabled_state_id = None
            suppresed_or_shelved = event.SuppressedOrShelved
            acked_state_text = str(event.AckedState.Text)
            acked_state_id = None
            condition_class_id = str(event.ConditionClassId)
            identifier = str(event.NodeId.Identifier)
            quality = str(event.Quality)
            retain = event.Retain

            if hasattr(event, "ActiveState/Id"):
                active_state_id = getattr(event, "ActiveState/Id")

            if hasattr(event, "EnabledState/Id"):
                enabled_state_id = getattr(event, "EnabledState/Id")

            if hasattr(event, "AckedState/Id"):
                acked_state_id = getattr(event, "AckedState/Id")

            logger_opcua_alarm.error(
                                    f"New event received from {self.address}:"
                                    f"Message: {message}"
                                    f"Date: {date}"
                                    f"State: {active_state_id}"
                                    f"Severity: {severity}"
                                    f"Enable state id: {enabled_state_id}"
                                    f"suppresed_or_shelved: {suppresed_or_shelved}"
                                    f"acknowledged state text: {acked_state_text}"
                                    f"acknowledged state: {acked_state_id}"
                                    f"condition class id: {condition_class_id}"
                                    f"Quality: {quality}"
                                    f"Retain: {retain}"
                                    f"identifier: {identifier}"
                                    )

            with open(self.phone_book_file, 'r', encoding='utf8') as f:
                    users = json.load(f)

            for user in users:
                if user.get('Active') == 'Yes':
                    phone_number = user.get('phone_number')
                    name = user.get('Namn')
                    message = f"Alarm detected! Message: {message}, Severity: {severity}"
                    send_sms(phone_number, message)
                    print(f"Sent SMS to {name} at {phone_number}")

        except Exception as e:
            logger_alarm.error(f"Error while processing event notification from {self.address} - Error: {e}")
            logger_alarm.error(traceback.format_exc())
            raise e


async def monitor_alarms():
    """
    This function monitors alarms by creating a subscription for each opcua server.
    """

    opcua_config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'configs', 'opcua_config.json')

    with open(opcua_config_file, 'r') as file:
            data = file.read()
            json_data = json.loads(data)
            ip_adress = json_data["adress"]
            username = json_data["username"]
            password = json_data["password"]

    await subscribe_to_server(ip_adress, username, password)