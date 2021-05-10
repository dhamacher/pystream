"""
Start UDP listener and send batches to Azure Event Hub.
"""
import socket
import os
import logging
from pathlib import Path
from datetime import datetime
from azure.eventhub.aio import EventHubProducerClient  # The package name suffixed with ".aio" for async
from azure.eventhub import EventData
import asyncio
import queue
import argparse
import yaml


""" Set the logging level."""
LOG_LEVEL = logging.WARNING
""" For optimal performance, theses values must be set."""
BUFFER_SIZE = 8196
SERVER = "localhost"

""" Set up logging."""
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%m/%d/%Y %I:%M:%S %p'
p = Path(__file__)
logging.basicConfig(format=LOG_FORMAT, datefmt=DATE_FORMAT, filename=f"{p.parents[0] / 'pystream-logs.txt'}", level=LOG_LEVEL)
log = logging.getLogger(__name__)



def start_consumer_loop(loop: asyncio.AbstractEventLoop,  q: queue.Queue) -> None:
    try:
        """ Set the event loop for the current thread."""
        asyncio.set_event_loop(loop)

        """ Eventhub connection string coming from environment variables."""
        CONNECTION_STR = os.environ['EVENT_HUB_CONN_STR']        
        EVENTHUB_NAME = os.environ['EVENT_HUB_NAME']

        """ Create the task and execute continuously."""
        loop.run_until_complete(consume(q, CONNECTION_STR, EVENTHUB_NAME))
    except Exception as e:
        log.exception(str(e))
        raise e


def start_producer_loop(loop: asyncio.AbstractEventLoop, q: queue.Queue, port: int) -> None:
    try:
        """ Set the event loop for the current thread."""
        asyncio.set_event_loop(loop)

        """ Eventhub connection string coming from environment variables."""
        CONNECTION_STR = os.environ['EVENT_HUB_CONN_STR']
        EVENTHUB_NAME = os.environ['EVENT_HUB_NAME']

        """ Bind three sockets that represent the backend that nginx load balances."""
        udp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        udp_socket.bind((SERVER, port))
        log.info(f"Socket bind successful on {SERVER}:{port}. Up since {str(datetime.now())}.")

        """ Create the task and execute continuously."""
        loop.run_until_complete(produce(q, udp_socket, CONNECTION_STR, EVENTHUB_NAME))
    except Exception as e:
        log.exception(str(e))
        raise e


async def produce(q: queue.Queue, sock: socket.socket, connection_str: str, evh_name: str):
    try:
        producer = EventHubProducerClient.from_connection_string(connection_str, eventhub_name=evh_name)
        log.debug("Reading from socket")
        while True:
            can_add = True
            event_data_batch = await producer.create_batch()
            while can_add:
                try:
                    payload, client = sock.recvfrom(BUFFER_SIZE)
                    event_data_batch.add(EventData(payload))
                    log.warning(payload)
                except ValueError as e:
                    can_add = False
                    q.put_nowait(event_data_batch)
                    log.debug("Batch inserted into Queue")
                    log.debug(f"Queue size: {q.qsize()}")
    except Exception as e:
        log.exception(str(e))


async def consume(q: queue.Queue, connection_str: str, evh_name: str):
    try:
        client = EventHubProducerClient.from_connection_string(connection_str, eventhub_name=evh_name)
        log.debug("Sending to Event Hub.")
        while True:
            if q.empty():
                log.warning("Queue is empty! Sleeping for 30 seconds.")
                await asyncio.sleep(30)
            else:
                batch = q.get(False)
                log.debug("Send Batch!")
                await client.send_batch(batch)
    except Exception as e:
        log.exception(str(e))
        raise e


async def run(port: int) -> None:
    try:
        """ Create thread-safe queue for communication between producer and consumers. """
        q = queue.Queue()

        """ Create a producer loop."""
        producer_loop = asyncio.new_event_loop()
        log.info("Producer thread created.")

        """ Create a consumer loop."""
        consumer_loop = asyncio.new_event_loop()
        log.info("Consumer thread created.")

        """ Start asyncio threads."""
        await asyncio.gather(
            asyncio.to_thread(start_producer_loop, producer_loop, q, port),
            asyncio.to_thread(start_consumer_loop, consumer_loop, q)
        )
    except Exception as e:
        log.exception(str(e))
        raise e


if __name__ == '__main__':
    try:
        """ Parse command line arguments."""
        parser = argparse.ArgumentParser(description='UDP Listener that sends incoming data to event hub.')
        parser.add_argument('--port', nargs='?', help="The port to bind the UDP socket to.", default='1444')
        args = parser.parse_args()
        port = int(args.port)
        asyncio.run(run(port))
    except Exception as e:
        log.exception(str(e))
