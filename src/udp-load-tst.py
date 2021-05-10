import socket
import datetime
import time
import json
import logging
from pathlib import Path


""" Settings."""
DEBUG = 0

BUFFER_SIZE = 8196
SERVER = "localhost"


HOST = '<host-ip>'
PORT = 35687
MESSAGE = "Hello World!"


""" Set the logging level."""
if DEBUG:    
    LOG_LEVEL = logging.DEBUG
else:
    LOG_LEVEL = logging.ERROR


def setup_logging(level):
    """ Set up logging."""
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    DATE_FORMAT = '%m/%d/%Y %I:%M:%S %p'
    p = Path(__file__)
    logging.basicConfig(format=LOG_FORMAT, datefmt=DATE_FORMAT, filename=f"{p.parents[0] / 'udp-tst.txt'}", level=level)
    log = logging.getLogger(__name__)

    return log


log = setup_logging(LOG_LEVEL)
try:   
    log.info(f"UDP target IP: {HOST}")
    log.info(f"UDP target port: {PORT}")
    log.info(f"message: {MESSAGE}")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        if DEBUG:
            log.debug("Sending Message")
            payload = bytes(f"Time: {datetime.datetime.now()} | Message: {MESSAGE}", "utf-8")
            sock.sendto(payload, (HOST, PORT))
            log.debug("Message Send!")
            time.sleep(1)
        else:            
            payload = bytes(f"Time: {datetime.datetime.now()} | Message: {MESSAGE}", "utf-8")
            sock.sendto(payload, (HOST, PORT))
except Exception as e:
    log.exception(str(e))
    time.sleep(10)
