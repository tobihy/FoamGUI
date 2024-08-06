import os
from enum import Enum, IntFlag, auto

SPACER = " "
TAB = "    "
NEWLINE = os.linesep

TYPE = "type"
VALUE = "value"
NONUNIFORM = "nonuniform"
UNIFORM = "uniform"


class ModelUpdateType(Enum):
    KEY = auto()
    VALUE = auto()


class ModelCreateType(Enum):
    BEFORE = auto()
    AFTER = auto()
    CHILD = auto()
    FILE = auto()


class ModelDeleteType(Enum):
    KEY_VALUE = auto()
    FILE = auto()
    CLEAR_DICT = auto()


class CaseDirMode(Enum):
    NEW = auto()
    EXISTING = auto()


class ODictType(Enum):
    ZERO_DIR = auto()
    SYSTEM_DIR = auto()
    CONSTANT_DIR = auto()
    OTHER_DIR = auto()
    FILE = auto()
    BOUNDARY_FIELD = auto()
    OTHER = auto()


class DictMenuFlag(IntFlag):
    NONE = auto()
    FILE = auto()
    SUB_DIR = auto()
    BOUNDARY_FIELD = auto()
