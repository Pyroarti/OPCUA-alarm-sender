from threading import Thread
import asyncio

from app import main as start_web_server
from opcua_alarm import monitor_alarms
from create_logger import setup_logger
from watchdog import main_watchdog

logger = setup_logger(__name__)


async def set_up_tasks():
    try:
        monitor_task = asyncio.create_task(monitor_alarms())
        watchdog_task = asyncio.create_task(main_watchdog("e", "e", "e"))
        await asyncio.gather(monitor_task, watchdog_task)
    except Exception as e:
        logger.error(f"Error in main AsyncIO loop: {e}")
        raise

def run_web_server():
    try:
        start_web_server()
    except Exception as e:
        logger.error(f"Error in Flask app: {e}")
        raise e


if __name__ == '__main__':

    web_server_thread = Thread(target=run_web_server)
    web_server_thread.start()

    asyncio.run(set_up_tasks())

