import serial
import time

# Initialize serial port
try:
    ser = serial.Serial('COM18', 115200, timeout=1)  # Replace 'COMPORT' with your COM port
    ser.flushInput()
except Exception as e:
    print(f"Failed to open serial port: {e}")
    exit(1)

# Function to send AT commands
def send_at(command, response, timeout=1):
    ser.write((command + '\r\n').encode())
    time.sleep(timeout)
    while True:
        if ser.inWaiting():
            break
    read_data = ser.read(ser.inWaiting()).decode()
    if response not in read_data:
        print(f"Failed to execute {command}: {read_data}")
        return False
    return True

# Setup modem
if not send_at('AT', 'OK'):
    print("Modem not responding. Exiting.")
    ser.close()
    exit(1)

if not send_at('AT+CMGF=1', 'OK'):  # Set modem to text mode
    print("Failed to set text mode. Exiting.")
    ser.close()
    exit(1)

# Send SMS
phone_number = '0720669637'  # Replace with the phone number you want to send to
message = 'Hello from raspberry pi'  # Replace with your message

if not send_at(f'AT+CMGS="{phone_number}"', '>'):
    print("Failed to set SMS parameters. Exiting.")
    ser.close()
    exit(1)

ser.write((message + chr(26)).encode())  # chr(26) is sending Ctrl+Z
time.sleep(3)

response = ser.read(ser.inWaiting()).decode()
if 'OK' in response:
    print("Message sent successfully.")
else:
    print(f"Failed to send message: {response}")

# Close serial port
ser.close()
