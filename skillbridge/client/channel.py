#------------------------------------------------------------------------------
# Import
#------------------------------------------------------------------------------
from select import select
from socket import AF_INET, SOCK_STREAM, socket
from sys import platform
from typing import Any, Iterable, TextIO, Type, Union
import re


#------------------------------------------------------------------------------
# Channel
#------------------------------------------------------------------------------
class Channel:

    #--------------------------------------------------------------------------
    # Constructor
    #--------------------------------------------------------------------------
    def __init__(self, max_transmission_length: int):
        self._max_transmission_length = max_transmission_length

    #--------------------------------------------------------------------------
    # Send
    #--------------------------------------------------------------------------
    def send(self, data: str) -> str:
        raise NotImplementedError  # pragma: no cover

    #--------------------------------------------------------------------------
    # close
    #--------------------------------------------------------------------------
    def close(self) -> None:
        raise NotImplementedError  # pragma: no cover

    #--------------------------------------------------------------------------
    # flush
    #--------------------------------------------------------------------------
    def flush(self) -> None:
        raise NotImplementedError  # pragma: no cover

    #--------------------------------------------------------------------------
    # Try to repair the connection
    #--------------------------------------------------------------------------
    def try_repair(self) -> Any:
        raise NotImplementedError  # pragma: no cover

    #--------------------------------------------------------------------------
    # Get maximum transmission length
    #--------------------------------------------------------------------------
    @property
    def max_transmission_length(self) -> int:
        return self._max_transmission_length

    #--------------------------------------------------------------------------
    # Set maximum transmission length
    #--------------------------------------------------------------------------
    @max_transmission_length.setter
    def max_transmission_length(self, value: int) -> None:
        self._max_transmission_length = value

    def __del__(self) -> None:
        try:
            self.close()
        except:  # noqa
            pass

    #--------------------------------------------------------------------------
    # Decode response
    #--------------------------------------------------------------------------
    @staticmethod
    def decode_response(response: str) -> str:
        status, response = response.split(' ', maxsplit=1)

        if status == 'failure':
            if response == '<timeout>':
                raise RuntimeError(
                    "Timeout: you should restart the skill server and "
                    "increase the timeout `pyStartServer ?timeout X`."
                )
            raise RuntimeError(response)
        return response

#------------------------------------------------------------------------------
# TCP Channel
#------------------------------------------------------------------------------
class TcpChannel(Channel):
    address_family = AF_INET
    socket_kind = SOCK_STREAM

    #--------------------------------------------------------------------------
    # Constructor
    #--------------------------------------------------------------------------
    def __init__(self):
        super().__init__(1_000_000)
        self.connected = False
        self.address = ('127.0.0.1', 52425)
        self.socket = self.start()

    #--------------------------------------------------------------------------
    # Start
    #--------------------------------------------------------------------------
    def start(self) -> socket:
        sock = socket(self.address_family , self.socket_kind)
        sock.settimeout(1)
        sock.connect(self.address)
        sock.settimeout(None)
        self.connected = True
        return sock
        
    #--------------------------------------------------------------------------
    # Reconnect the socket
    #--------------------------------------------------------------------------
    def reconnect(self) -> None:
        self.socket.close()
        self.socket = self.start()

    #--------------------------------------------------------------------------
    # Send data
    #--------------------------------------------------------------------------
    def _send_only(self, data: str) -> None:
        if len(data) > self._max_transmission_length:
            got = len(data)
            should = self._max_transmission_length
            raise ValueError(f'Data exceeds max transmission length {got} > {should}')

        data = "{:10}{}".format(len(data), data)
        try:
            self.socket.sendall(data.encode())
        except (BrokenPipeError, OSError):
            print("attempting to reconnect")
            self.reconnect()
            self.socket.sendall(data.encode())

    #--------------------------------------------------------------------------
    # Receive all
    #--------------------------------------------------------------------------
    def _receive_all(self, remaining: int) -> Iterable[bytes]:
        data = b''
        while remaining:
            chunk = self.socket.recv(remaining)
            remaining -= len(chunk)
            data = data + chunk
        return data

    #--------------------------------------------------------------------------
    # Receive
    #--------------------------------------------------------------------------
    def _receive_only(self) -> str:
        try:
            received_length_raw = self._receive_all(10)
        except KeyboardInterrupt:
            raise RuntimeError(
                "Receive aborted, you should restart the skill server or"
                " call `ws.try_repair()` if you are sure that the response"
                " will arrive."
            ) from None

        if not received_length_raw:
            raise RuntimeError("The server unexpectedly died")
        received_length = int(received_length_raw)
        response = self._receive_all(received_length).decode()
        return self.decode_response(response)

    #--------------------------------------------------------------------------
    # Send
    #--------------------------------------------------------------------------
    def send(self, data: str) -> str:
        self._send_only(data)
        return self._receive_only()

    #--------------------------------------------------------------------------
    # Close connection
    #--------------------------------------------------------------------------
    def close(self) -> None:
        if self.connected:
            self._send_only('close')
            self.socket.close()
            self.connected = False

    #--------------------------------------------------------------------------
    # Flush channel
    #--------------------------------------------------------------------------
    def flush(self) -> None:
        while True:
            read, _, _ = select([self.socket], [], [], 0.1)
            if read:
                length = int(self.socket.recv())
                self.socket.recv(length)
            else:
                break

#------------------------------------------------------------------------------
# Windows
#------------------------------------------------------------------------------
if platform == 'win32':

    def create_channel_class() -> Type[TcpChannel]:
        class WindowsChannel(TcpChannel):
            def configure(self, sock: socket) -> None:
                try:
                    from socket import SIO_LOOPBACK_FAST_PATH  # type: ignore

                    sock.ioctl(SIO_LOOPBACK_FAST_PATH, True)  # type: ignore
                except ImportError:
                    pass
        return WindowsChannel
        
#------------------------------------------------------------------------------
# Linux
#------------------------------------------------------------------------------
else:

    def create_channel_class() -> Type[TcpChannel]:

        class UnixChannel(TcpChannel):
            pass
        return UnixChannel
