import serial
import time
import asyncio


async def send_sms(phone_number, message):
    try:
        ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
        ser.flushInput()

        async def send_at(command, response, timeout=1):
            ser.write((command + '\r\n').encode())
            await asyncio.sleep(timeout)
            while ser.inWaiting():
                break
            read_data = ser.read(ser.inWaiting()).decode()
            if response not in read_data:
                raise Exception(f"Failed to execute {command}: {read_data}")

        await send_at('AT', 'OK')
        await send_at('AT+CMGF=1', 'OK')
        await send_at(f'AT+CMGS="{phone_number}"', '>')
        ser.write((message + chr(26)).encode())
        await asyncio.sleep(3)

        response = ser.read(ser.inWaiting()).decode()
        if 'OK' not in response:
            raise Exception(f"Failed to send message: {response}")

        ser.close()
        print("Message sent successfully.")
    except Exception as e:
        print(f"Failed to send SMS: {e}")
        if ser:
            ser.close()
