import socket
import datetime
import time 
from pathlib import Path
import logging


""" Settings."""
DEBUG = 0

HOST = '<host-ip>'
PORT = 39576
MESSAGE = "Hello World!"


""" Set the logging level."""
if DEBUG:
    LOG_LEVEL = logging.DEBUG
else:
    LOG_LEVEL = logging.INFO


def setup_logging(level):
    """ Set up logging."""
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    DATE_FORMAT = '%m/%d/%Y %I:%M:%S %p'
    p = Path(__file__)
    logging.basicConfig(format=LOG_FORMAT, datefmt=DATE_FORMAT, filename=f"{p.parents[0] / 'tcp-tst.txt'}", level=level)
    log = logging.getLogger(__name__)

    return log


log = setup_logging(LOG_LEVEL)

log.info(f"TCP target IP: {HOST}")
log.info(f"TCP target port: {PORT}")
log.info(f"message: {MESSAGE}")

try:
    id = 0
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        while True:
            if DEBUG:
                log.debug("Sending next msg")
                payload = f"Time: {datetime.datetime.now()} | Message: {MESSGAE}"
                s.sendall(payload.encode())
                log.debug("Send")
                time.sleep(1)
            else:                
                payload = f"ID: {id} | Time: {datetime.datetime.now()} | Message: {MESSAGE}"
                s.sendall(payload.encode())
except Exception as e:
    log.exception(str(e))
    time.sleep(1)
