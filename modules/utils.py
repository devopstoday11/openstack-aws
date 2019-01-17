"""
Utility functions
"""
import json
from logging.config import dictConfig
import dateutil.parser

class WorkloadException(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)

class ImageConverterException(Exception):  
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)

class BotoException(Exception):  
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)

def get_data(filepath):
    """
    Read data from JSON and returns dictionary
    """
    with open(filepath, 'r') as filepointer:
        str_data = filepointer.read()
        data = json.loads(str_data)
    return data

def load_data(filepath, data):
    """
    Dumps the data into json file
    """
    with open(filepath, 'w') as filepointer:
        json.dump(data, filepointer, indent=4)
    return True

def get_time(iso_time):
    """
    converts ISO time format to UTC
    """
    return dateutil.parser.parse(iso_time).strftime('%Y-%m-%d %H:%M:%S.%f')[:19]

def bytes_to_mb(val_in_bytes):
    """
    Converts Bytes to MB
    """
    if isinstance(val_in_bytes, int):
        return round(float(val_in_bytes/(1024.0*1024.0)), 2)
    elif isinstance(val_in_bytes, str):
        val_in_bytes = int(val_in_bytes)
        return round(float(val_in_bytes/(1024.0*1024.0)), 2)
    return None

FORMAT = "%(asctime)s {app} [%(thread)d]\
%(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]"

def setup_logging(name, level="INFO", fmt=FORMAT):
    """
    logger
    """
    formatted = fmt.format(app=name)
    logging_config = {
        "version": 1,
        'disable_existing_loggers': False,
        "formatters": {
            'standard': {
                'format': formatted
            }
        },
        "handlers": {
            'default': {
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
                'level': level,
                'stream': 'ext://sys.stdout'
            },
            'console': {
                'level': level,
                'class': 'logging.StreamHandler',
                'formatter': 'standard'
            },
            'file': {
                'level': level,
                'class': 'logging.FileHandler',
                'formatter': 'standard',
                'filename': 'trilio.log',
            },
        },
        "loggers": {
            "": {
                'handlers': ['file'],
                'level': level
            }
        }
    }

    dictConfig(logging_config)
