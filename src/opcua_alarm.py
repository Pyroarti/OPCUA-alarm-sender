import asyncio
from asyncua import ua
import os
import json

from create_logger import setup_logger
from opcua_client import connect_opcua
from sms_sender import send_sms

logger_alarm = setup_logger('opcua_prog_alarm')
logger_opcua_alarm = setup_logger("opcua_alarms")

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
config_dir = os.path.join(parent_dir, "configs")
phone_book_file = os.path.join(config_dir, 'phone_book.json')
opcua_config_file = os.path.join(config_dir, 'opcua_config.json')


async def subscribe_to_server(adresses: str, username: str, password: str):
    client = None
    while True:
        try:
            if client is None:
                client = await connect_opcua(adresses, username, password)

            # Check if client is None before creating a subscription
            if client is not None:
                handler = SubHandler(adresses)
                sub = await client.create_subscription(1000, handler)
                alarmConditionType = client.get_node("ns=0;i=2915")
                server_node = client.get_node(ua.NodeId(Identifier=2253, NodeIdType=ua.NodeIdType.Numeric, NamespaceIndex=0))
                await sub.subscribe_alarms_and_conditions(server_node, alarmConditionType)

            else:
                logger_alarm.error(f"Connection to server {adresses} failed. Retrying...")
                await asyncio.sleep(10)

        except Exception as e:
            logger_alarm.error(f"Error connecting or subscribing to server {adresses}: {e}")
            await client.disconnect()
            client = None
            await asyncio.sleep(10)

class SubHandler:
    def __init__(self, address: str):
        self.address = address

    async def event_notification(self, event):

        try:
            opcua_alarm_message = str(event.Message.Text)
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
                                    f"Message: {opcua_alarm_message}"
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

            with open(phone_book_file, 'r', encoding='utf8') as f:
                users = json.load(f)

            for user in users:
                if user.get('Active') == 'Yes':
                    phone_number = user.get('phone_number')
                    name = user.get('Namn')
                    message = f"Medelande från Elmo pumpstation: {opcua_alarm_message}"
                    send_sms(phone_number, message)
                    logger_opcua_alarm.info(f"Sent SMS to {name} at {phone_number}")

        except Exception as e:
            logger_alarm.error(f"Error while processing event notification from {self.address} - Error: {e}")


async def monitor_alarms():
    with open(opcua_config_file, 'r') as file:
        json_data = json.load(file)
        ip_address = json_data["adress"]
        username = json_data["username"]
        password = json_data["password"]

    await subscribe_to_server(ip_address, username, password)
