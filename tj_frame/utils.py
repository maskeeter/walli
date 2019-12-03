import json
import logging
from multiprocessing import Pipe, Process

from tj_frame import screen

LOGS_PATH = 'logs'
LOG_FORMAT = '%(asctime)s - %(message)s'


def read_config(path):
    try:
        with open(path, 'rt') as config_file:
            config_source = config_file.read()
        if config_source:
            return json.loads(config_source)
    except FileNotFoundError:
        logging.warning(f"config file {path} not found")
    except ValueError:
        logging.warning(f"config file {path} not valid")
    return None


def validate_url(url: str, validation: str = None):
    if url:
        if not validation or url.find(validation) > 0:
            return url
        else:
            logging.warning("url is not valid")
    else:
        logging.warning("url field is empty")
    return None


def run_in_separate_process(func):
    def wrapper(*args, **kwargs):
        parent_conn, child_conn = Pipe()
        arguments = list(args)
        arguments.append(child_conn)
        process = Process(target=func, name=func.__name__, args=arguments, kwargs=kwargs)
        process.start()
        return process, parent_conn

    return wrapper


def get_file_logger(file_name):
    logger = logging.getLogger(file_name)
    f_handler = logging.FileHandler(f'{LOGS_PATH}/{file_name}.log')
    f_handler.setLevel(logging.DEBUG)
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    f_handler.setFormatter(f_format)
    logger.addHandler(f_handler)
    return logger


def kill_app(message: str = None):
    screen.turn_off()
    if message:
        logging.exception(message)


def list_updated(list_id: str):
    if list_updated.list_id != list_id:
        list_updated.list_id = list_id
        return True
    return False


list_updated.list_id = ''

# TODO: WRAPPER DECORATOR TO MAINTAIN PLAYER IF IT CRASHES
# try
# func
# except DBusConnectionError as e:
# pass
# except OMXPlayerDeadError as e:
# pass
# except FileNotFoundError as e:
# pass
