import time

import serial

from create_logger import setup_logger
from config_handler import ConfigHandler


####################################

logger = setup_logger(__name__)

config_manager = ConfigHandler()
sms_config = config_manager.sms_config

PORT:str = sms_config["port"]
TIMEOUT:int = sms_config["timeout"]
MAX_RETRIES:int = sms_config["max_retries"]
BAUDRATE:int = sms_config["baudrate"]

####################################


def send_at(ser:serial, command:str, response:str, timeout:int, max_retries:int):
    """
    Send AT command to GSM modem and check for response.

    Parameters
    ----------
    ser: Serial object
    command: AT command to send
    response: Expected response
    timeout: Timeout in seconds
    max_retries: Max number of retries
    """

    retries = 0
    while retries <= max_retries:
        try:
            ser.write((command + '\r\n').encode())
            time.sleep(timeout)
            while ser.inWaiting():
                break
            read_data = ser.read(ser.inWaiting()).decode()
            if response in read_data:
                return  # Success
            else:
                logger.error(f"Failed to execute {command}: {read_data}")
        except Exception as e:
            logger.error(f"Error executing {command}: {e}")

        retries += 1
        time.sleep(5)

    logger.error(f"Max retries reached for command {command}. Giving up.")


def send_sms(phone_number: str, message: str):
    """
    Send SMS using GSM modem.
    Parameters
    ----------
    phone_number: Phone number to send SMS to
    message: Message to send
    """

    try:
        with serial.Serial(port=PORT, baudrate=BAUDRATE, timeout=TIMEOUT) as ser:

            send_at(ser=ser, command='AT', response='OK',timeout=TIMEOUT, max_retries=MAX_RETRIES)

            send_at(ser=ser, command='AT+CMGF=1', response='OK', timeout=TIMEOUT, max_retries=MAX_RETRIES)

            send_at(ser=ser, command='AT+CSCS="UCS2"', response='OK', timeout=TIMEOUT, max_retries=MAX_RETRIES)

            phone_number_hex = phone_number.encode('utf-16-be').hex().upper()

            send_at(ser=ser, command=f'AT+CMGS="{phone_number_hex}"', response='>', timeout=TIMEOUT, max_retries=MAX_RETRIES)

            message_hex = message.encode('utf-16-be').hex().upper()  # Convert the message to UCS-2 hex string
            ser.write((message_hex + chr(26)).encode())  # chr(26) is the ASCII code for CTRL+Z

            response = ser.read(ser.in_waiting).decode("utf-8")
            logger.info(response)
            if 'OK' not in response:
                logger.error(f"Failed to send SMS to {phone_number}: {response}")
            else:
                logger.info("Message sent successfully.")

    except serial.SerialException as e:
        logger.error(f"Serial Exception: {e}")
    except Exception as e:
        logger.error(f"General Exception: {e}")

