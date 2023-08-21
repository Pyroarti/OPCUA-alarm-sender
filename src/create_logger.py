import logging
import os
import sys

def setup_logger(logger_name):

    """
    Creates and configures a logging instance for the specified module.

    This function creates a logger with the provided logger_name, sets its level to DEBUG,
    and associates it with a file handler that writes to a log file. The log file is stored
    in a 'logs' directory or 'alarms' directory depending on the logger_name.

    Parameters:
    logger_name (str): The name of the logger. This will be the name of the module where the
    logger is used.

    Usage:
    ```
    logger = setup_logger('module_name')
    ```

    This will create a logger that writes messages to the 'module_name.log' file in the 'logs'
    directory. If the logger_name is 'alarms', it will write to the 'alarms' directory instead.
    """

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    if getattr(sys, 'frozen', False):
        app_path = sys._MEIPASS
    else:
        app_path = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(app_path)

    alarms = "alarms"
    log_folder = "logs"

    if logger_name  != "alarms":

        log_dir = os.path.abspath(os.path.join(parent_dir, log_folder))
        os.makedirs(log_dir, exist_ok=True)

    else:
        log_dir = os.path.abspath(os.path.join(parent_dir, alarms))
        os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f"{logger_name}.log")
    formatter = logging.Formatter('%(asctime)s|%(levelname)s|%(name)s|%(message)s', datefmt='%Y:%m:%d %H:%M:%S')

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    logger.addHandler(file_handler)

    return logger