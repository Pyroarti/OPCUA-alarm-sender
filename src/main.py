from threading import Thread
import asyncio

from app import main as start_flask_app
from opcua_alarm import monitor_alarms

def start_asyncio_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(monitor_alarms())

if __name__ == '__main__':
    asyncio_thread = Thread(target=start_asyncio_loop)

    asyncio_thread.start()

    start_flask_app()

    asyncio_thread.join()
