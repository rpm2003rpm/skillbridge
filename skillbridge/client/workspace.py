#------------------------------------------------------------------------------
# Import
#------------------------------------------------------------------------------
from functools import partial
from typing import Any, Iterable, cast
from .channel import create_channel_class, Channel
from .functions import FunGroup, RemoteFunction
from .globals import DirectGlobals, Globals
from .hints import Symbol
from .objects import RemoteObject, RemoteTable, RemoteVector
from .translator import DefaultTranslator, Translator

#------------------------------------------------------------------------------
# Workspace class
#------------------------------------------------------------------------------
class Workspace:

    #--------------------------------------------------------------------------
    # Constructor
    #--------------------------------------------------------------------------
    def __init__(self, channel: Channel) -> None:
        self._channel = channel
        self._translator = self._prepare_default_translator()
        self._max_transmission_length = 1_000_000
        self.__ = DirectGlobals(channel, self._translator)
        self._  = FunGroup(channel, self._translator)


    #--------------------------------------------------------------------------
    # Prepare the translator
    #--------------------------------------------------------------------------
    def _prepare_default_translator(self) -> DefaultTranslator:
        translator = DefaultTranslator()
        types = [('Remote', RemoteObject), 
                 ('Table', RemoteTable), 
                 ('Vector', RemoteVector)]

        for name, typ in types:
            construct = partial(typ, self._channel, translator)
            translator.register_new_context(name, construct)
        return translator

    #--------------------------------------------------------------------------
    # Make table
    #--------------------------------------------------------------------------
    def make_table(self, 
                   name: str, 
                   default: Any = Symbol('unbound')) -> RemoteTable:
        return self['makeTable'](name, default)  # type: ignore

    #--------------------------------------------------------------------------
    # Make vector
    #--------------------------------------------------------------------------
    def make_vector(self, 
                    length: int, 
                    default: Any = Symbol('unbound')) -> RemoteVector:
        return self['makeVector'](length, default)  # type: ignore

    #--------------------------------------------------------------------------
    # Globals
    #--------------------------------------------------------------------------
    def globals(self, prefix: str) -> Globals:
        return Globals(self._channel, self._translator, prefix)
 
    #--------------------------------------------------------------------------
    # Return item
    #--------------------------------------------------------------------------
    def __getitem__(self, item: str) -> RemoteFunction:
        return RemoteFunction(self._channel, item, self._translator)

    #--------------------------------------------------------------------------
    # Flush channel
    #--------------------------------------------------------------------------
    def flush(self) -> None:
        self._channel.flush()

    #--------------------------------------------------------------------------
    # Define a function
    #--------------------------------------------------------------------------
    def define(self, name: str, args: Iterable[str], code: str) -> None:
        code = code.replace('\n', ' ')
        skill_name = name
        skill_name = skill_name[0].upper() + skill_name[1:]
        arg_list = ' '.join(arg for arg in args)
        code = f'defun(user{skill_name} ({arg_list}) {code})'
        cast(Symbol, self._translator.decode(self._channel.send(code)))

    #--------------------------------------------------------------------------
    # Open a communication channel
    #--------------------------------------------------------------------------
    @classmethod
    def open(cls, log_exception: bool = True) -> 'Workspace':
        try:
            channel_class = create_channel_class()
            channel = channel_class()
        except:
            raise RuntimeError("Failed to open a comunication channel")
        return Workspace(channel)

    #--------------------------------------------------------------------------
    # Close the communication channel
    #--------------------------------------------------------------------------
    def close(self, log_exception: bool = True) -> None:
        try:
            self._channel.close()
        except:  # noqa
            raise RuntimeError("Failed to close the comunication channel")

    #--------------------------------------------------------------------------
    # Get maximum transmission length
    #--------------------------------------------------------------------------
    @property
    def max_transmission_length(self) -> int:
        return self._channel.max_transmission_length

    #--------------------------------------------------------------------------
    # Set maximum transmission length
    #--------------------------------------------------------------------------
    @max_transmission_length.setter
    def max_transmission_length(self, value: int) -> None:
        self._channel.max_transmission_length = value

    #--------------------------------------------------------------------------
    # try to repare the connection
    #--------------------------------------------------------------------------
    def try_repair(self) -> Any:
        return self._channel.try_repair()
