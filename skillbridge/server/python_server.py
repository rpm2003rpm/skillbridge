#-------------------------------------------------------------------------------
# Import
#-------------------------------------------------------------------------------
import logging
import socket
from SocketServer import BaseRequestHandler, TCPServer, ThreadingMixIn
from argparse import ArgumentParser
from logging import WARNING, basicConfig, getLogger
from os import getenv
from select import select
from sys import argv, stderr, stdin, stdout
import re


#-------------------------------------------------------------------------------
# Logger instance
#-------------------------------------------------------------------------------
LOG_PATH = str(getenv("SKILLBRIDGE_LOG_DIRECTORY"))
if not LOG_PATH:
    LOG_PATH = '.'
LOG_FILE = '{0}/skillbridge_server.log'.format(LOG_PATH)
LOG_FORMAT = '%(asctime)s %(levelname)s %(message)s'
LOG_DATE_FORMAT = '%d.%m.%Y %H:%M:%S'
LOG_LEVEL = WARNING
basicConfig(filename=LOG_FILE, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
logger = getLogger("python-server")


#-------------------------------------------------------------------------------
# Send commands to the standard output
#-------------------------------------------------------------------------------
def send_to_skill(data):
    stdout.write(data)
    stdout.write("\n")
    stdout.flush()


#-------------------------------------------------------------------------------
# Is data ready
#-------------------------------------------------------------------------------
def data_ready(timeout):
    readable, _, _ = select([stdin], [], [], timeout)
    return bool(readable)


#-------------------------------------------------------------------------------
# Read commands from standard input
#-------------------------------------------------------------------------------
def read_from_skill(timeout):
    readable = data_ready(timeout)
    if readable:
        return stdin.readline()
    logger.debug("timeout")
    return 'failure <timeout>'


#-------------------------------------------------------------------------------
# Server class
#-------------------------------------------------------------------------------
class Server(ThreadingMixIn, TCPServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)


#-------------------------------------------------------------------------------
# Handler class
#-------------------------------------------------------------------------------
class Handler(BaseRequestHandler):

    #--------------------------------------------------------------------------
    # Receive all
    #--------------------------------------------------------------------------
    def _receive_all(self, remaining):
        data = b''
        while remaining:
            chunk = self.request.recv(remaining)
            remaining -= len(chunk)
            data = data + chunk
        return data

    #---------------------------------------------------------------------------
    # handle one request 
    # receive data from socket, sent it to the standard output, recieive 
    # answer from standard output, and send it back to socket.
    #---------------------------------------------------------------------------
    def handle_one_request(self):
        length = self._receive_all(10)
        if not length:
            logger.warning("client {0} lost connection".format(self.client_address))
            return False
        logger.debug("got length {0}".format(length))

        length = int(length)
        command = self._receive_all(length)

        logger.debug("received {0} bytes".format(len(command)))

        if command.startswith(b'close'):
            logger.debug("client {0} disconnected".format(self.client_address))
            return False
        logger.debug("got data {0}".format(command[:1000].decode()))

        send_to_skill(command.decode())
        logger.debug("sent data to skill")
        result = read_from_skill(self.server.skill_timeout).encode()  # type: ignore
        logger.debug("got response from skill {0}".format(result[:1000]))

        result = '%10s%s' % (len(result), result)
        self.request.send(result.encode())
        logger.debug("sent response to client")
        return True

    #---------------------------------------------------------------------------
    # Try to handle one rquest. Log the exception if it fails
    #---------------------------------------------------------------------------
    def try_handle_one_request(self):
        try:
            return self.handle_one_request()
        except Exception as e:
            logger.exception(e)
            return False

    #---------------------------------------------------------------------------
    # handle
    # once connected call try_handle_one_request in a loop
    #---------------------------------------------------------------------------
    def handle(self):
        logger.info("client {0} connected".format(self.client_address))
        client_is_connected = True
        while client_is_connected:
            client_is_connected = self.try_handle_one_request()


#-------------------------------------------------------------------------------
# Main
#-------------------------------------------------------------------------------
def main(nid, log_level, timeout):
    logger.setLevel(getattr(logging, log_level))

    server = Server(("0.0.0.0", 52425), Handler)
    server.skill_timeout = timeout

    logger.info(
        "starting server id={0} log={1} timeout={2}".format(nid, 
                                                            log_level,
                                                            timeout)
    )
    server.serve_forever()


#-------------------------------------------------------------------------------
# Process input arguments and call main
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    log_levels = "DEBUG WARNING INFO ERROR CRITICAL FATAL".split()
    argument_parser = ArgumentParser(argv[0])
    argument_parser.add_argument('id')
    argument_parser.add_argument('log_level', choices=log_levels)
    argument_parser.add_argument('--timeout', type=float, default=None)

    ns = argument_parser.parse_args()

    try:
        main(ns.id, ns.log_level, ns.timeout)
    except KeyboardInterrupt:
        pass
