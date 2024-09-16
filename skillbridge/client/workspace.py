#------------------------------------------------------------------------------
# Import
#------------------------------------------------------------------------------
from functools import partial
from typing import Any, Iterable, cast
from socket import AF_INET, SOCK_STREAM
from .channel import create_channel_class, Channel
from .remote import Functions, Variables, RemoteObject, RemoteTable, RemoteVector
from .hints import Symbol, SkillCode, Skill, Union
from .translator import DefaultTranslator, Translator


#------------------------------------------------------------------------------
# Workspace class
#------------------------------------------------------------------------------
class Workspace:

    #--------------------------------------------------------------------------
    # Constructor
    #--------------------------------------------------------------------------
    def __init__(self, 
                 address = ('127.0.0.1', 52425), 
                 family = AF_INET,
                 kind = SOCK_STREAM):
        try:
            channel_class = create_channel_class()
            channel = channel_class(address, family, kind)
        except:
            raise RuntimeError("Failed to open a comunication channel")
        self._channel = channel
        self._translator = self._prepare_default_translator()
        self._max_transmission_length = 1_000_000
        self.variables = Variables(channel, self._translator)
        self.functions = Functions(channel, self._translator)
        self._  = self.functions
        self.__ = self.variables

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
    # Execute raw code
    #--------------------------------------------------------------------------
    def runSkillCode(self, code : Union[str, SkillCode]) -> Skill:
        return self._translator.decode(self._channel.send(code))

    #--------------------------------------------------------------------------
    # Flush channel
    #--------------------------------------------------------------------------
    def flush(self) -> None:
        self._channel.flush()

    #--------------------------------------------------------------------------
    # Close the communication channel
    #--------------------------------------------------------------------------
    def close(self) -> None:
        try:
            #clean up
            code = 'foreach(elem listVariables("^__py_openfile.*") if(portp(elem) then close(elem))) ' +\
                   'foreach(elem listVariables("^__py_.*") set(elem `unbound)) t'
            self._channel.send(code)
        except:
            pass
        try:
            self.functions.gc()
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
