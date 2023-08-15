#------------------------------------------------------------------------------
# Import
#------------------------------------------------------------------------------
from typing import TYPE_CHECKING, Any, Dict, List, NamedTuple, \
                   NewType, Set, Tuple, Union


if TYPE_CHECKING:  # pragma: no cover
    from typing_extensions import Protocol
else:
    class Protocol:
        pass


__all__ = [
    'Number',
    'Symbol',
    'Key',
    'SkillComponent',
    'SkillCode',
    'Skill',
    'Definition',
    'Function',
    'SkillTuple',
    'SkillList',
    'SupportsReprSkill',
]

Number = Union[int, float]
SkillComponent = Union[int, str]
SkillCode = NewType('SkillCode', str)


class Function(NamedTuple):
    name: str
    description: str
    aliases: Set[str]


Definition = List[Function]


class SupportsReprSkill(Protocol):
    def __repr_skill__(self) -> SkillCode:  # pragma: no cover
        ...


if TYPE_CHECKING:  # pragma: no cover
    from .var import Var

    Skill = Union[
        Var, SupportsReprSkill, Number, str, bool, None, 'SkillList', 'SkillDict', 'SkillTuple'
    ]
else:
    Skill = Any


class SkillList(List[Skill]):
    pass


class SkillTuple(Tuple[Skill, ...]):
    pass


class SkillDict(Dict[str, Skill]):
    pass


class Symbol():
    
    def __init__(self, value):
        self.value = value

    def __repr_skill__(self) -> SkillCode:
        if not isinstance(self.value, str):
            raise AttributeError("error")
        return SkillCode(f"'{self.value}")
        
    def __str__(self) -> str:
        return f"Symbol({self.value})"

    def __repr__(self) -> str:
        return f"Symbol({self.value})"


class Key(NamedTuple):
    name: str

    def __repr_skill__(self) -> SkillCode:
        return SkillCode(f"?{self.name}")

    def __str__(self) -> str:
        return f"Key({self.name})"

    def __repr__(self) -> str:
        return f"Key({self.name})"
