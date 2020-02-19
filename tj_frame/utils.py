import json
import logging
import random
import string
import threading
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


def read_options(config_path: str):
    with open(config_path) as config_file:
        config = config_file.read()
        return [arg for arg in config.split('\n') if len(arg) and arg[0] != '#']


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


def run_in_thread(fn):
    def wrapper(*k, **kw):
        t = threading.Thread(target=fn, args=k, kwargs=kw, daemon=True)
        t.start()
        return t

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


def id_generator(size=6, chars=string.ascii_letters):
    return ''.join(random.choice(chars) for _ in range(size))


def toggle(cycle_list: list, current: int) -> int:
    return current + 1 if current < len(cycle_list) - 1 else 0
