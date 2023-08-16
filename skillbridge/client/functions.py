#------------------------------------------------------------------------------
# Import
#------------------------------------------------------------------------------
from typing import List
from .channel import Channel
from .hints import Key, Skill, SkillCode
from .translator import Translator
from .var import Var


#------------------------------------------------------------------------------
# Keys. Not quite sure what it does
#------------------------------------------------------------------------------
def keys(**attrs: Skill) -> List[Skill]:
    return [flat for key, value in attrs.items() for flat in (Key(key), value)]


#------------------------------------------------------------------------------
# Function group. Used only once in the _ attribute of workspace. Any attribute
# of this class will return a RemoteFunction.
#------------------------------------------------------------------------------
class FunGroup:

    #--------------------------------------------------------------------------
    # Constructor
    #--------------------------------------------------------------------------
    def __init__(self, channel: Channel, translator: Translator) -> None:
        self._channel = channel
        self._translate = translator

    #--------------------------------------------------------------------------
    # Find a group of functions
    #--------------------------------------------------------------------------        
    def __getattr__(self, item: str) -> 'RemoteFunction':
        return RemoteFunction(self._channel, f'{item}', self._translate)


#------------------------------------------------------------------------------
# RemoteFunction. Class to send a function to the server and get back the 
# results. 
#------------------------------------------------------------------------------
class RemoteFunction:

    #--------------------------------------------------------------------------
    # Constructor
    #--------------------------------------------------------------------------
    def __init__(self, 
                 channel: Channel, 
                 func: str, 
                 translator: Translator) -> None:
        self._channel = channel
        self._translate = translator
        self._function = func
        
    #--------------------------------------------------------------------------
    # When a RemoteFunction class is called, the function name is encoded, 
    # a message is sent to the server, and the result is decode and 
    # returned.
    #--------------------------------------------------------------------------
    def __call__(self, *args: Skill, **kwargs: Skill) -> Skill:
        command = self.encode_call(*args, **kwargs)
        result = self._channel.send(command)
        return self._translate.decode(result)
        
    #--------------------------------------------------------------------------
    # econde the functtion call
    #--------------------------------------------------------------------------
    def encode_call(self, *args: Skill, **kwargs: Skill) -> SkillCode:
        #name = snake_to_camel(self._function)
        return self._translate.encode_call(self._function, *args, **kwargs)

    #--------------------------------------------------------------------------
    # Encode the function call and creae a variable with it.
    #--------------------------------------------------------------------------
    def var(self, *args: Skill, **kwargs: Skill) -> Var:
        return Var(__class__.encode_call(self, *args, **kwargs))

    #--------------------------------------------------------------------------
    # Representation of a remote function returns the help menu for the 
    # function
    #--------------------------------------------------------------------------
    def __repr__(self) -> str:
        command = self._translate.encode_help(self._function)
        result = self._channel.send(command)
        return self._translate.decode_help(result)
