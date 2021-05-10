"""
Start UDP listener and send batches to Azure Event Hub.
"""
import os
import socket
import logging
from multiprocessing import get_context, Pipe
from pathlib import Path
from datetime import datetime
from azure.eventhub.aio import EventHubProducerClient  # The package name suffixed with ".aio" for async
from azure.eventhub import EventData
import asyncio
import argparse

""" Set the logging level."""
LOG_LEVEL = logging.WARNING

""" For optimal performance, theses values must be set."""
BUFFER_SIZE = 8196
SERVER = "localhost"


def setup_logging(level):
    """ Set up logging."""
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    DATE_FORMAT = '%m/%d/%Y %I:%M:%S %p'
    p = Path(__file__)
    logging.basicConfig(format=LOG_FORMAT, datefmt=DATE_FORMAT, filename=f"{p.parents[0] / 'aiompnode.txt'}", level=level)
    log = logging.getLogger(__name__)

    return log


log = setup_logging(LOG_LEVEL)


def start_consumer_loop(loop: asyncio.AbstractEventLoop, p: Pipe, conn_str: str, evh_name: str) -> None:
    try:
        """ Set the event loop for the current thread."""
        asyncio.set_event_loop(loop)

        """ Create the task and execute continuously."""
        loop.run_until_complete(consume(p, conn_str, evh_name))
    except Exception as e:
        log.exception(str(e))
        raise e


def start_producer_loop(loop: asyncio.AbstractEventLoop, p: Pipe, sock: socket) -> None:
    try:
        """ Set the event loop for the current thread."""
        asyncio.set_event_loop(loop)

        """ Create the task and execute continuously."""
        loop.run_until_complete(produce(p, sock))
    except Exception as e:
        log.exception(str(e))
        raise e


async def produce(p: Pipe, sock: socket.socket):
    try:
        log.debug("Reading from socket")
        while True:
            try:
                payload, client = sock.recvfrom(BUFFER_SIZE)
                p.send(payload)
            except Exception as e:
                log.exception(str(e))
    except Exception as e:
        log.exception(str(e))


async def consume(p: Pipe, connection_str: str, evh_name: str):
    try:
        client = EventHubProducerClient.from_connection_string(connection_str, eventhub_name=evh_name)
        log.debug("Sending to Event Hub.")
        while True:
            batch = await client.create_batch()
            can_add = True
            while can_add:
                try:
                    data = p.recv()
                    batch.add(EventData(data))
                except ValueError as e:
                    log.debug("Batch full. Sending...")
                    can_add = False
                    log.debug("Batch send!")
            await client.send_batch(batch)
            log.debug("Send Batch!")
    except Exception as e:
        log.exception(str(e))
        raise e


def run_producer(p: Pipe, sock: socket) -> None:
    try:
        """ Create thread-safe queue for communication between producer and consumers. """
        pipe = p

        """ Create a producer loop."""
        producer_loop = asyncio.new_event_loop()
        log.info("Producer thread created.")

        """ Start producer loop."""
        start_producer_loop(producer_loop, pipe, sock)
    except Exception as e:
        log.exception(str(e))
        raise e


def run_consumer(p: Pipe, conn_str: str, evh_name: str) -> None:
    try:
        """ Create thread-safe queue for communication between producer and consumers. """
        pipe = p

        """ Create a consumer loop."""
        consumer_loop = asyncio.new_event_loop()
        log.info("Consumer thread created.")

        """ Start asyncio threads."""
        start_consumer_loop(consumer_loop, pipe, conn_str, evh_name)
    except Exception as e:
        log.exception(str(e))
        raise e


if __name__ == '__main__':
    # TODO: Use yaml config files to configure nodes for TCP and UDP,
    try:
        """ Parse command line arguments."""
        parser = argparse.ArgumentParser(description='UDP Listener that sends incoming data to event hub.')
        parser.add_argument('--port', nargs='?', help="The port to bind the UDP socket to.", default='1444')
        args = parser.parse_args()
        port = int(args.port)

        """ Create context to create the processes."""
        context = get_context("spawn")

        """Get a pipe! Returns a pair (conn1, conn2) of Connection objects representing the ends of a pipe. The pipe is
        unidirectional: conn1 can only be used for receiving messages and conn2 can only be used for 
        sending messages."""
        psink, psource = context.Pipe()

        """ Eventhub connection string and event hub name."""
        CONNECTION_STR = os.environ['EVENT_HUB_CONN_STR']        
        EVENTHUB_NAME = os.environ['EVENT_HUB_NAME']

        """ Bind the socket that listens for incoming data."""
        udp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        udp_socket.bind((SERVER, 1444))
        log.info(f"Socket bind successful on {SERVER}:{port}. Up since {str(datetime.now())}.")

        """ Create child processes for consumer and producer."""
        consumer_process = context.Process(target=run_consumer, args=(psource, CONNECTION_STR, EVENTHUB_NAME,))
        producer_process = context.Process(target=run_producer, args=(psink, udp_socket,))

        consumer_process.start()
        producer_process.start()
    except Exception as e:
        log.exception(str(e))