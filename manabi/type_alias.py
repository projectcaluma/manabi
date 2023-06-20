from typing import Any, Dict, List, Optional, Tuple, Union

try:
    from typing import TypeAlias

    TypeType = Union[type, TypeAlias]
except ImportError:
    # Older python versions do not support TypeAlias
    TypeType = Any  # type: ignore

PropType = Union[
    int,
    List["PropType"],
    str,
    None,
    Dict[str, "PropType"],
    Tuple["PropType"],
    bool,
]
OptionalProp = Optional[PropType]