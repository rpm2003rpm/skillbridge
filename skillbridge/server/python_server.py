#-------------------------------------------------------------------------------
# Import
#-------------------------------------------------------------------------------
import logging
import socket
from SocketServer import BaseRequestHandler, ThreadingMixIn, TCPServer, UnixStreamServer
from argparse     import ArgumentParser
from logging      import WARNING, basicConfig, getLogger
from os           import getenv
from select       import select
from sys          import argv, stderr, stdin, stdout
import re
import os


#-------------------------------------------------------------------------------
# Logger instance
#-------------------------------------------------------------------------------
LOG_PATH = getenv("SKILLBRIDGE_LOG_DIRECTORY")
if not LOG_PATH:
    LOG_PATH = '.'
LOG_PATH = str(LOG_PATH)
LOG_FILE        = '{0}/skillbridge_server.log'.format(LOG_PATH)
LOG_FORMAT      = '%(asctime)s %(levelname)s %(message)s'
LOG_DATE_FORMAT = '%d.%m.%Y %H:%M:%S'
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
class Server(TCPServer): #, ThreadingMixIn):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)


#-------------------------------------------------------------------------------
# Server class
#-------------------------------------------------------------------------------
class ServerLocal(UnixStreamServer): #, ThreadingMixIn):
    def server_bind(self):
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

        if command.startswith(b'$close_remote_connection$'):
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
        logger.info("client {0} disconnected".format(self.client_address))


#-------------------------------------------------------------------------------
# Main
#-------------------------------------------------------------------------------
def main(log_level, timeout, address):
    logger.setLevel(getattr(logging, log_level))

    pattern = r"[ ]*([0-9]+.[0-9]+.[0-9]+.[0-9])[ ]*,[ ]*([0-9]*)[ ]*"
   
    if(re.search(pattern, address)):
        m = re.findall(pattern, address)[0]
        server = Server((m[0], int(m[1])), Handler)
    else:
        try:
            os.unlink(address)
        except OSError:
            if os.path.exists(address):
                raise
        server = ServerLocal(address, Handler)
    server.skill_timeout = timeout
    logger.info("starting server addr={0} log={1} timeout={2}".format(address, 
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
    argument_parser.add_argument('address', type=str, default="0.0.0.0,52425")
    argument_parser.add_argument('log_level', choices=log_levels)
    argument_parser.add_argument('--timeout', type=float, default=None)
    ns = argument_parser.parse_args()

    try:
        main(ns.log_level, ns.timeout, ns.address)
    except KeyboardInterrupt:
        pass
