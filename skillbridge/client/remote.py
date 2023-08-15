#------------------------------------------------------------------------------
# Import
#------------------------------------------------------------------------------
from .channel import Channel
from .hints import Skill, SkillCode
from .translator import Translator


#------------------------------------------------------------------------------
# Remote variable
#------------------------------------------------------------------------------
class RemoteVariable:
    _attributes = {'_channel', '_variable', '_translator'}

    #--------------------------------------------------------------------------
    # Constructor
    #--------------------------------------------------------------------------
    def __init__(self, 
                 channel: Channel, 
                 translator: Translator, 
                 variable: SkillCode) -> None:
        self._channel = channel
        self._variable = variable
        self._translator = translator

    #--------------------------------------------------------------------------
    # Skill code representation
    #--------------------------------------------------------------------------   
    def __repr_skill__(self) -> SkillCode:
        return SkillCode(self._variable)

    #--------------------------------------------------------------------------
    # string representation
    #-------------------------------------------------------------------------- 
    def __repr__(self) -> str:
        return self.__str__()

    #--------------------------------------------------------------------------
    # Call function. 
    # Translate the function call to skill
    # Send the command
    # Convert the result back to python
    #-------------------------------------------------------------------------- 
    def _call(self, function: str, *args: Skill, **kwargs: Skill) -> Skill:
        code = self._translator.encode_call(function, *args, **kwargs)
        result = self._channel.send(code)
        return self._translator.decode(result)
