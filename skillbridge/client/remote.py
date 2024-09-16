#------------------------------------------------------------------------------
# Import
#------------------------------------------------------------------------------
from typing import List, Any, Tuple, Union, Iterable, Iterator, \
                   MutableMapping, cast, Optional
from .channel import Channel
from .hints import Skill, SkillCode, Symbol, Unbound
from .translator import Translator, ParseError


#------------------------------------------------------------------------------
# Check if it is jupyter magic 
#------------------------------------------------------------------------------
def is_jupyter_magic(attribute: str) -> bool:
    ignore = {
        '_ipython_canary_method_should_not_exist_',
        '_ipython_display_',
        '_repr_mimebundle_',
        '_repr_html_',
        '_repr_markdown_',
        '_repr_svg_',
        '_repr_png_',
        '_repr_pdf_',
        '_repr_jpeg_',
        '_repr_latex_',
        '_repr_json_',
        '_repr_javascript_',
        '_rapped',
        '__wrapped__',
        '__call__',
    }
    return attribute in ignore


#------------------------------------------------------------------------------
# Remote class
#------------------------------------------------------------------------------
class Remote():
    _attributes = ["_identifier", "_translator", "_channel"] 

    #--------------------------------------------------------------------------
    # Constructor
    #--------------------------------------------------------------------------
    def __init__(self, 
                 channel: Channel, 
                 translator: Translator, 
                 identifier: str) -> None:
        self._channel = channel
        self._translator = translator
        self._identifier = identifier

    #--------------------------------------------------------------------------
    # Call
    #--------------------------------------------------------------------------
    def _call(self, *args: Skill, **kwargs: Skill) -> Skill:
        code = self._translator.encode_call(*args, **kwargs)
        response = self._channel.send(code)
        return self._translator.decode(response)

    #--------------------------------------------------------------------------
    # Call
    #--------------------------------------------------------------------------
    def __call__(self, *args: Skill, **kwargs: Skill) -> Skill:
        return self._call(self._identifier, *args, **kwargs)

    #--------------------------------------------------------------------------
    # String representation
    #-------------------------------------------------------------------------- 
    def __str__(self) -> str:
        return f"<remote {self._identifier}>"

    #--------------------------------------------------------------------------
    # String representation
    #-------------------------------------------------------------------------- 
    def __repr__(self) -> str:
        return self.__str__()


#------------------------------------------------------------------------------
# RemoteFunction. Class to send a function to the server and get back the 
# results. 
#------------------------------------------------------------------------------
class RemoteFunction(Remote):

    #--------------------------------------------------------------------------
    # Representation of a remote function returns the help menu for the 
    # function
    #--------------------------------------------------------------------------
    def __repr__(self) -> str:
        command = self._translator.encode_help(self._identifier)
        result = self._channel.send(command)
        return self._translator.decode_help(result)


#------------------------------------------------------------------------------
# Remote variable
#------------------------------------------------------------------------------
class RemoteVariable(Remote):

    #--------------------------------------------------------------------------
    #  Assign with lshift?
    #--------------------------------------------------------------------------
    def __lshift__(self, code: Any) -> None:
        code = self._translator.encode_assign(self._identifier, code)
        result = self._channel.send(command)
        assert self._translator.decode(response) is None

    #--------------------------------------------------------------------------
    # Skill code representation
    #--------------------------------------------------------------------------   
    def __repr_skill__(self) -> SkillCode:
        return SkillCode(self._identifier)


#------------------------------------------------------------------------------
# Remote Object
#------------------------------------------------------------------------------
class RemoteObject(RemoteVariable):

    #--------------------------------------------------------------------------
    # Help
    #--------------------------------------------------------------------------
    def __dir__(self) -> List[str]:
        code = self._translator.encode_dir(self._identifier)
        response = self._channel.send(code)
        attributes = self._translator.decode_dir(response.strip())
        return attributes

    #--------------------------------------------------------------------------
    # Get attributes
    #--------------------------------------------------------------------------
    def __getitem__(self, key: str) -> Skill:
        code = self._translator.encode_getattr(self._identifier, key)
        response = self._channel.send(code)
        return self._translator.decode(response)

    #--------------------------------------------------------------------------
    # Set attribute
    #--------------------------------------------------------------------------
    def __setitem__(self, key: str, value: Skill) -> Skill:
        code = self._translator.encode_setattr(self._identifier, key, value)
        response = self._channel.send(code)
        assert self._translator.decode(response) is None

    #--------------------------------------------------------------------------
    # Get attribute
    #--------------------------------------------------------------------------
    def __getattr__(self, key: str) -> Any:
        if is_jupyter_magic(key):
            raise AttributeError(key)
        return self[key]

    #--------------------------------------------------------------------------
    # Set attribute
    #--------------------------------------------------------------------------
    def __setattr__(self, key: str, value: Any) -> None:
        if key in Remote._attributes:
            return super().__setattr__(key, value)
        self[key] = value

    #--------------------------------------------------------------------------
    # Pointer to attribute. Don't access the attribute directly.
    #--------------------------------------------------------------------------
    def pattr(self, key : str) -> Any:
        code = self._translator.encode_getattr(self._identifier, key)
        return RemoteObject(self._channel, self._translator, code)

    #--------------------------------------------------------------------------
    # Check if it is an open file
    #--------------------------------------------------------------------------
    def _is_open_file(self) -> bool:
        return self._identifier.startswith('__py_openfile_')

    #--------------------------------------------------------------------------
    # Encode dir
    #--------------------------------------------------------------------------
    def __dir__(self) -> Iterable[str]:
        if self._is_open_file():
            return super().__dir__()
        code = self._translator.encode_dir(self._identifier)
        response = self._channel.send(code)
        attributes = self._translator.decode_dir(response.strip())
        return attributes

    #--------------------------------------------------------------------------
    # Get doc
    #--------------------------------------------------------------------------
    def getdoc(self) -> str:
        return "Properties:\n- " + '\n- '.join(dir(self))

    #--------------------------------------------------------------------------
    # Equal test
    #--------------------------------------------------------------------------
    def __eq__(self, other: Any) -> bool:
        if isinstance(other, RemoteObject):
            return self._identifier == other._identifier
        return NotImplemented

    #--------------------------------------------------------------------------
    # Not equal
    #--------------------------------------------------------------------------
    def __ne__(self, other: Any) -> bool:
        if isinstance(other, RemoteObject):
            return self._identifier != other._identifier
        return NotImplemented


#------------------------------------------------------------------------------
# Collection
#------------------------------------------------------------------------------
class RemoteCollection(RemoteVariable):

    #--------------------------------------------------------------------------
    # String representation
    #--------------------------------------------------------------------------
    def __str__(self) -> str:
        return f'<remote {self._call("lsprintf", "%L", self)}>'

    #--------------------------------------------------------------------------
    # Length
    #--------------------------------------------------------------------------
    def __len__(self) -> int:
        return cast(int, self._call('length', self))

    #--------------------------------------------------------------------------
    # Get item
    #--------------------------------------------------------------------------
    def __getitem__(self, item: Skill) -> Skill:
        return self._call('arrayref', self, item)

    #--------------------------------------------------------------------------
    # Set item
    #--------------------------------------------------------------------------
    def __setitem__(self, key: Skill, value: Skill) -> None:
        self._call('setarray', self, key, value)

    #--------------------------------------------------------------------------
    # Delete item
    #--------------------------------------------------------------------------
    def __delitem__(self, item: Skill) -> None:
        self._call('remove', item, self)


#------------------------------------------------------------------------------
# Table
#------------------------------------------------------------------------------
class RemoteTable(RemoteCollection, MutableMapping[Skill, Skill]):

    #--------------------------------------------------------------------------
    # Get item
    #--------------------------------------------------------------------------
    def __getitem__(self, item: Skill) -> Skill:
        try:
            return super().__getitem__(item)
        except ParseError:
            raise KeyError(item) from None

    #--------------------------------------------------------------------------
    # Get attribute
    #--------------------------------------------------------------------------
    def __getattr__(self, item: str) -> Skill:
        return self[item]

    #--------------------------------------------------------------------------
    # Set attribute
    #--------------------------------------------------------------------------
    def __setattr__(self, key: str, value: Skill) -> None:
        if key in Remote._attributes:
            super().__setattr__(key, value)
        else:
            self[key] = value

    #--------------------------------------------------------------------------
    # Iterator
    #--------------------------------------------------------------------------
    def __iter__(self) -> Iterator[Skill]:
        code = self._translator.encode_getattr(self.__repr_skill__(), '?')
        result = self._channel.send(code)
        return iter(self._translator.decode(result) or ())  # type: ignore


#------------------------------------------------------------------------------
# Vector
#------------------------------------------------------------------------------
class RemoteVector(RemoteCollection):

    _msg = "list index {} out of range (len={})"
    _contains = "array index out of bounds"

    #--------------------------------------------------------------------------
    # Get item
    #--------------------------------------------------------------------------
    def __getitem__(self, item: Skill) -> Skill:
        try:
            return super().__getitem__(item)
        except RuntimeError as e:
            if RemoteVector._contains in str(e):
                raise IndexError(RemoteVector._msg.format(item, len(self))) from None
            raise  # pragma: no cover
        except ParseError:
            raise IndexError(RemoteVector._msg.format(item, len(self))) from None

    def __setitem__(self, item: Skill, value: Skill) -> None:
        try:
            super().__setitem__(item, value)
        except RuntimeError as e:
            if RemoteVector._contains in str(e):
                raise IndexError(RemoteVector._msg.format(item, len(self))) from None
            raise  # pragma: no cover


#------------------------------------------------------------------------------
# Access classes
#------------------------------------------------------------------------------
class Access():

    #--------------------------------------------------------------------------
    # Constructor
    #--------------------------------------------------------------------------
    def __init__(self, 
                 channel: Channel, 
                 translator: Translator) -> None:
        self._channel = channel
        self._translator = translator

    #--------------------------------------------------------------------------
    # Find a group of functions
    #--------------------------------------------------------------------------        
    def __getattr__(self, item: str) -> Any:
        if is_jupyter_magic(item):
            raise AttributeError(item)
        return self[item]

    #--------------------------------------------------------------------------
    # List variables starting with start
    #--------------------------------------------------------------------------
    def startswith(self, start) -> Iterable[str]:
        _type = self.__class__.__name__
        code = self._translator.encode_call(f'list{_type}', f"^{start}.*")
        response = self._channel.send(code)
        return self._translator.decode_dir(response)


#------------------------------------------------------------------------------
# Globals
#------------------------------------------------------------------------------
class Variables(Access):

    _attributes = ["_translator", "_channel"]

    #--------------------------------------------------------------------------
    # Return item
    #--------------------------------------------------------------------------
    def __getitem__(self, item: str) -> RemoteVariable:
        if item.isidentifier():
            code = self._translator.encode_read_variable(item)
            response = self._channel.send(code)
            return self._translator.decode(response)
        raise AttributeError(item)

    #--------------------------------------------------------------------------
    # Set item
    #--------------------------------------------------------------------------
    def __setitem__(self, item: str, value: Any) -> Any:
        code = self._translator.encode_assign(item, value)
        response = self._channel.send(code)
        assert self._translator.decode(response) is None

    #--------------------------------------------------------------------------
    # Set attribute
    #--------------------------------------------------------------------------
    def __setattr__(self, key: str, value: Any) -> None:
        if key in Variables._attributes:
            return super().__setattr__(key, value)
        self[key] = value

    #--------------------------------------------------------------------------
    # Delete item
    #--------------------------------------------------------------------------
    def __delitem__(self, item: str):
        self[item] = Unbound

    #--------------------------------------------------------------------------
    # Delete attrinute
    #--------------------------------------------------------------------------
    def __delattr__(self, item: str):
        del self[item]


#------------------------------------------------------------------------------
# Function group. Used only once in the _ attribute of workspace. Any attribute
# of this class will return a RemoteFunction.
#------------------------------------------------------------------------------
class Functions(Access):

    #--------------------------------------------------------------------------
    # Find a group of functions
    #-------------------------------------------------------------------------- 
    def __getitem__(self, item: str) -> RemoteFunction:
        return RemoteFunction(self._channel, self._translator, f'{item}')

