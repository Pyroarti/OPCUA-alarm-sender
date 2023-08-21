import time
import json
from serial import Serial


def setup_serial(port, baudrate=115200, timeout=1)-> Serial:
    return Serial(port, baudrate, timeout=timeout)


def send_at_command(ser: Serial, command, wait_time=1):
    ser.write((command + "\r\n").encode())
    time.sleep(wait_time)
    response = ser.readlines()
    return [line.decode('utf-8').strip() for line in response]


def send_sms(ser: Serial, phone_number, message):
    send_at_command(ser, "AT+CMGF=1")  # Set the module to text mode
    send_at_command(ser, f'AT+CMGS="{phone_number}"', 2)
    ser.write((message + chr(26)).encode())  # End the message with Ctrl+Z (ASCII 26)


def main():
    with open('data.json', 'r') as file:
        data = json.load(file)
        phone_number = data['phone_number']

    ser: Serial = setup_serial('/dev/ttyS0')

    if not ser.is_open():
        print("Failed to open serial port")
        return

    # Initialize the module
    send_at_command(ser, "AT")

    # Send SMS
    message = "Hello world"
    send_sms(ser, phone_number, message)

    ser.close()

if __name__ == '__main__':
    main()
