#------------------------------------------------------------------------------
# Import
#------------------------------------------------------------------------------
from json import dumps, loads
from re import findall, sub
from typing import Any, Callable, Dict, Iterable, List, NoReturn, Optional,\
                   Union, cast
from warnings import warn_explicit
from .hints import Skill, SkillCode, Symbol


#------------------------------------------------------------------------------
# Parse Error class
#------------------------------------------------------------------------------
class ParseError(Exception):
    pass


#------------------------------------------------------------------------------
# Raise error if errors are found
#------------------------------------------------------------------------------
def _raise_error(message: str) -> NoReturn:
    raise ParseError(message)


#------------------------------------------------------------------------------
# Raise error if errors are found
#------------------------------------------------------------------------------
def _show_warning(message: str, result: Any) -> Any:
    for i, line in enumerate(message.splitlines(keepends=False)):
        warn_explicit(line.lstrip("*WARNING*"), UserWarning, "Skill response", i)
    return result


#------------------------------------------------------------------------------
# Context for evaluating a string containing python code
#------------------------------------------------------------------------------
_STATIC_EVAL_CONTEXT = {
    'Symbol': Symbol,
    'error': _raise_error,
    'warning': _show_warning,
}


#------------------------------------------------------------------------------
# Evaluate a string containing python code
#------------------------------------------------------------------------------
def _skill_value_to_python(string: str, 
                     eval_context: Optional[Dict[str, Any]] = None) -> Skill:
    return eval(string, eval_context or _STATIC_EVAL_CONTEXT)  # type: ignore


#------------------------------------------------------------------------------
# Convert a python expression to skill
#------------------------------------------------------------------------------
def python_value_to_skill(value: Skill) -> SkillCode:

    try:
        return value.__repr_skill__()  # type: ignore
    except AttributeError:
        pass

    if isinstance(value, Symbol):
        return SkillCode(f"'{python_value_to_skill(value.value)}")
    
    if isinstance(value, dict):
        items = ' '.join(f"'{key} {python_value_to_skill(value)}" \
                for key, value in value.items())
        return SkillCode(f'list(nil {items})')

    if value is False or value is None:
        return SkillCode('nil')

    if value is True:
        return SkillCode('t')

    if isinstance(value, (int, float, str)):
        return SkillCode(dumps(value))

    if isinstance(value, (tuple)):
        inner = ' '.join(python_value_to_skill(item) for item in value)
        return SkillCode(f'({inner})')

    if isinstance(value, (list)):
        inner = ' '.join(python_value_to_skill(item) for item in value)
        return SkillCode(f'(list {inner})')

    type_ = type(value).__name__
    raise RuntimeError(f"Cannot convert object {type_!r} to skill.") from None


#------------------------------------------------------------------------------
# build skill path
#------------------------------------------------------------------------------
def build_skill_path(components: Iterable[Union[str, int]]) -> SkillCode:
    it = iter(components)
    path = str(next(it))

    for component in it:
        if isinstance(component, int):
            path = f'(nth {component} {path})'
        else:
            path = f'{path}->{component}'

    return SkillCode(path)


#------------------------------------------------------------------------------
# Translator class
#------------------------------------------------------------------------------
class Translator:

    #--------------------------------------------------------------------------
    # Encode a skill function call
    #--------------------------------------------------------------------------
    @staticmethod
    def encode_call(func_name: str, *args: Skill, **kwargs: Skill) -> SkillCode:
        args_code = ' '.join(map(python_value_to_skill, args))
        kw_keys = kwargs
        kw_values = map(python_value_to_skill, kwargs.values())
        kwargs_code = ' '.join(f'?{key} {value}' \
                               for key, value in zip(kw_keys, kw_values))
        return SkillCode(f'{func_name}({args_code} {kwargs_code})')

    #--------------------------------------------------------------------------
    # Encode a dir call
    #--------------------------------------------------------------------------
    @staticmethod
    def encode_dir(obj: SkillCode) -> SkillCode:
        parts = ' '.join(
            (
                f'{obj}->?',
                f"if( type({obj}) == 'rodObj then {obj}->systemHandleNames)",
                f'if( type({obj}) == \'rodObj then {obj}->userHandleNames)',
            )
        )
        code = f'mapcar(lambda((attr) sprintf(nil "%s" attr)) nconc({parts}))'
        return SkillCode(code)

    #--------------------------------------------------------------------------
    # Decode dir call
    #--------------------------------------------------------------------------
    @staticmethod
    def decode_dir(code: str) -> List[str]:
        attributes = _skill_value_to_python(code) or ()
        return [str(attr) for attr in cast(List[str], attributes)]

    #--------------------------------------------------------------------------
    # Decode dir call
    #--------------------------------------------------------------------------
    @staticmethod
    def encode_getattr(obj: SkillCode, key: str) -> SkillCode:
        return build_skill_path([obj, key])

    #--------------------------------------------------------------------------
    # Encode read variable
    #--------------------------------------------------------------------------
    @staticmethod
    def encode_read_variable(name: str) -> SkillCode:
        return SkillCode(name)

    #--------------------------------------------------------------------------
    # Encode assign to variable
    #--------------------------------------------------------------------------
    def encode_assign(self, variable: str, value: Any) -> SkillCode:
        encoded_value = self.encode(value)
        return SkillCode(f'{variable} = {encoded_value} nil')

    #--------------------------------------------------------------------------
    # Encode help
    #--------------------------------------------------------------------------
    @staticmethod
    def encode_help(symbol: str) -> SkillCode:
        code = f"""
            _text = outstring()
            poport = _text help({symbol})
            poport = stdout getOutstring(_text)
        """.replace(
            "\n", " "
        )
        return SkillCode(code)

    #--------------------------------------------------------------------------
    # Decode help
    #--------------------------------------------------------------------------
    @staticmethod
    def decode_help(help_: str) -> str:
        return loads(help_)  # type: ignore

    #--------------------------------------------------------------------------
    # Encode set attibute
    #--------------------------------------------------------------------------
    @staticmethod
    def encode_setattr(obj: SkillCode, key: str, value: Any) -> SkillCode:
        code = build_skill_path([obj, key])
        value = python_value_to_skill(value)
        return SkillCode(f'{code} = {value}')

    #--------------------------------------------------------------------------
    # Encode
    #--------------------------------------------------------------------------
    def encode(self, value: Skill) -> SkillCode:
        raise NotImplementedError

    #--------------------------------------------------------------------------
    # Decode
    #--------------------------------------------------------------------------
    def decode(self, code: str) -> Skill:
        raise NotImplementedError


#------------------------------------------------------------------------------
# Encode set attibute
#------------------------------------------------------------------------------
class DefaultTranslator(Translator):

    #--------------------------------------------------------------------------
    # Constructor
    #--------------------------------------------------------------------------
    def __init__(self) -> None:
        self.context = _STATIC_EVAL_CONTEXT.copy()

    #--------------------------------------------------------------------------
    # register a new context for translation
    #--------------------------------------------------------------------------
    def register_new_context(self, 
                             name: str, 
                             constructor: Callable[[str], Skill]) -> None:
        self.context[name] = constructor
        
    #--------------------------------------------------------------------------
    # Encode
    #--------------------------------------------------------------------------
    def encode(self, value: Skill) -> SkillCode:
        return python_value_to_skill(value)

    #--------------------------------------------------------------------------
    # Decode
    #--------------------------------------------------------------------------
    def decode(self, code: str) -> Skill:
        return _skill_value_to_python(code, self.context)
