#------------------------------------------------------------------------------
# Import
#------------------------------------------------------------------------------
from typing import TYPE_CHECKING, Any, Dict, List, \
                   NamedTuple, NewType, Set, Tuple, Union

if TYPE_CHECKING:  # pragma: no cover
    from .var import Var
    Skill = Union[
        Var, Number, str, bool, None, SkillList, SkillDict, SkillTuple
    ]
else:
    Skill = Any

Number = Union[int, float]
SkillComponent = Union[int, str]
SkillCode = NewType('SkillCode', str)

class Function(NamedTuple):
    name: str
    description: str
    aliases: Set[str]

Definition = List[Function]

class SkillList(List[Skill]):
    pass

class SkillTuple(Tuple[Skill, ...]):
    pass

class SkillDict(Dict[str, Skill]):
    pass

class Symbol():
    
    def __init__(self, value):
        self.value = value

    def __str__(self) -> str:
        return f"{self.value}"

    def __repr__(self) -> str:
        return self.__str__()

    def __repr_skill__(self) -> Skill:
        if isinstance(self.value, str):
            return f"'{self.value}"
        raise AttributeError

Unbound = Symbol('unbound')
