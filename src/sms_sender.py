import serial
import time
from create_logger import setup_logger

logger = setup_logger(__name__)

def send_at(ser, command, response, timeout=2, max_retries=3):
    """"
    Send AT command to GSM modem and check for response.
    :param ser: Serial object
    :param command: AT command to send
    :param response: Expected response
    :param timeout: Timeout in seconds
    :param max_retries: Max number of retries
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
        time.sleep(2)

    logger.error(f"Max retries reached for command {command}. Giving up.")


def send_sms(phone_number: str, message: str):
    """
    Send SMS to a phone number using a GSM modem connected to the Raspberry Pi.
    The modem is conmmected to the raspberrys USB port.
    :param phone_number: Phone number to send SMS to
    :param message: Message to send
    """

    try:
        with serial.Serial('/dev/ttyUSB0', 115200, timeout=2) as ser:
            send_at(ser, 'AT', 'OK')
            send_at(ser, 'AT+CMGF=1', 'OK')
            send_at(ser, f'AT+CMGS="{phone_number}"', '>')

            ser.write((message + chr(26)).encode()) # chr(26) is the ASCII code for CTRL+Z (end of message)
            time.sleep(3)

            response = ser.read(ser.in_Waiting()).decode() # Read response from modem
            if 'OK' not in response:
                logger.error(f"Failed to send SMS to {phone_number}: {response}")

        logger.info("Message sent successfully.")

    except serial.SerialException as e:
        logger.error(f"Serial Exception: {e}")
    except Exception as e:
        logger.error(f"General Exception: {e}")
