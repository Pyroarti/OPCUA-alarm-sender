from threading import Thread
import asyncio

from app import main as start_web_server
from opcua_alarm import monitor_alarms
from create_logger import setup_logger

logger = setup_logger(__name__)


def start_asyncio_loop():

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(monitor_alarms())
    except Exception as e:
        logger.error(f"Error in asyncio loop: {e}")
        raise e


if __name__ == '__main__':

    asyncio_thread = Thread(target=start_asyncio_loop)
    asyncio_thread.start()

    try:
        start_web_server()
    except Exception as e:
        logger.error(f"Error in Flask app: {e}")
        raise e

    asyncio_thread.join()
