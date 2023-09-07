import serial
import time
from create_logger import setup_logger

logger = setup_logger(__name__)

def send_sms(phone_number, message):
    try:
        ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
        ser.flushInput()

        def send_at(command, response, timeout=1):
            ser.write((command + '\r\n').encode())
            time.sleep(timeout)
            while ser.inWaiting():
                break
            read_data = ser.read(ser.inWaiting()).decode()
            if response not in read_data:
                raise Exception(f"Failed to execute {command}: {read_data}")

        send_at('AT', 'OK')
        send_at('AT+CMGF=1', 'OK')
        send_at(f'AT+CMGS="{phone_number}"', '>')
        ser.write((message + chr(26)).encode())
        time.sleep(3)

        response = ser.read(ser.inWaiting()).decode()
        if 'OK' not in response:
            raise Exception(f"Failed to send message: {response}")

        ser.close()
        logger.info("Message sent successfully.")
    except Exception as e:
        logger.error(f"Failed to send SMS: {e}")
        if ser:
            ser.close()
