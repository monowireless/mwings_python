# -*- coding:utf-8 -*-
# Written for Python 3.12
# Formatted with Black

# MWings common defs

from __future__ import annotations

from struct import unpack
from enum import IntEnum, StrEnum, auto
from datetime import datetime, timezone, tzinfo
from collections import OrderedDict
from collections.abc import Sequence, MutableSequence, Iterable
from json import dumps
from abc import ABC, abstractmethod
from importlib import metadata
import platform
from typing import (
    Any,
    Callable,
    TypeVar,
    final,
    overload,
    TYPE_CHECKING,
)

from overrides import override
from pydantic_core import CoreSchema, core_schema
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    GetCoreSchemaHandler,
    computed_field,
    field_serializer,
    field_validator,
)
from pydantic.types import AwareDatetime

from . import utils


try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    if TYPE_CHECKING:
        raise ImportError("pandas required for dev")
    else:
        PANDAS_AVAILABLE = False


Timezone: tzinfo = timezone.utc
"""Global tzinfo"""


SomeCallable = TypeVar("SomeCallable", bound=Callable[..., Any])
"""TypeVar for handlers"""


class DtypedDecimal(ABC):
    def get_dtype(self) -> str:
        """Provide dtype info for pandas

        Returns
        -------
        str
            dtype identifier
        """

        return "int64"

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        """Override the pydantic schema for serialization

        For JSON, serialize as plain int or float.
        For dict, serialize as object of subclass derived from int or float.

        Parameters
        ----------
        source_type : Any
            The class we are generating a schema for.
        handler : GetCoreSchemaHandler
            Call into Pydantic's internal schema generation.

        Returns
        -------
        CoreSchema
            A `pydantic-core` `CoreSchema`
        """

        return core_schema.json_or_python_schema(
            json_schema=core_schema.decimal_schema(),
            python_schema=core_schema.any_schema(),
        )


class UInt8(int, DtypedDecimal):
    def __new__(cls, value: int | None = None) -> UInt8:
        """Create immutable instance

        Parameters
        ----------
        value : int, optional
            Value to set

        Returns
        -------
        UInt8
            Wrapped value

        Raises
        ------
        ValueError
            Out of range
        """

        if value is None:
            value = 0
        if not (0 <= value < 2**8):
            raise ValueError("The given value is out of the range")
        return super(UInt8, cls).__new__(cls, value)

    @override
    def get_dtype(self) -> str:
        """Provide dtype info for pandas

        Returns
        -------
        str
            dtype identifier
        """

        return "uint8"

    def hex(self) -> str:
        """Returns hex representation

        python `hex()` function does not accept object of subclass
        derived from int.

        Returns
        -------
        str
            Hex string (lower case)
        """

        return f"{self:02x}"


class Int8(int, DtypedDecimal):
    def __new__(cls, value: int | None = None) -> Int8:
        """Create immutable instance

        Parameters
        ----------
        value : int, optional
            Value to set

        Returns
        -------
        Int8
            Wrapped value

        Raises
        ------
        ValueError
            Out of range
        """

        if value is None:
            value = 0
        if not (-(2**7) <= value < 2**7):
            raise ValueError("The given value is out of the range")
        return super(Int8, cls).__new__(cls, value)

    @override
    def get_dtype(self) -> str:
        """Provide dtype info for pandas

        Returns
        -------
        str
            dtype identifier
        """

        return "int8"

    def hex(self) -> str:
        """Returns hex representation

        python `hex()` function does not accept object of subclass
        derived from int.

        Returns
        -------
        str
            Hex string (lower case)
        """

        return f"{self:02x}"


class UInt16(int, DtypedDecimal):
    def __new__(cls, value: int | None = None) -> UInt16:
        """Create immutable instance

        Parameters
        ----------
        value : int, optional
            Value to set

        Returns
        -------
        UInt16
            Wrapped value

        Raises
        ------
        ValueError
            Out of range
        """

        if value is None:
            value = 0
        if not (0 <= value < 2**16):
            raise ValueError("The given value is out of the range")
        return super(UInt16, cls).__new__(cls, value)

    @override
    def get_dtype(self) -> str:
        """Provide dtype info for pandas

        Returns
        -------
        str
            dtype identifier
        """

        return "uint16"

    def hex(self) -> str:
        """Returns hex representation

        python `hex()` function does not accept object of subclass
        derived from int.

        Returns
        -------
        str
            Hex string (lower case)
        """

        return f"{self:04x}"


class Int16(int, DtypedDecimal):
    def __new__(cls, value: int | None = None) -> Int16:
        """Create immutable instance

        Parameters
        ----------
        value : int, optional
            Value to set

        Returns
        -------
        Int16
            Wrapped value

        Raises
        ------
        ValueError
            Out of range
        """

        if value is None:
            value = 0
        if not (-(2**15) <= value < 2**15):
            raise ValueError("The given value is out of the range")
        return super(Int16, cls).__new__(cls, value)

    @override
    def get_dtype(self) -> str:
        """Provide dtype info for pandas

        Returns
        -------
        str
            dtype identifier
        """

        return "int16"

    def hex(self) -> str:
        """Returns hex representation

        python `hex()` function does not accept object of subclass
        derived from int.

        Returns
        -------
        str
            Hex string (lower case)
        """

        return f"{self:04x}"


class UInt32(int, DtypedDecimal):
    def __new__(cls, value: int | None = None) -> UInt32:
        """Create immutable instance

        Parameters
        ----------
        value : int, optional
            Value to set

        Returns
        -------
        UInt32
            Wrapped value

        Raises
        ------
        ValueError
            Out of range
        """

        if value is None:
            value = 0
        if not (0 <= value < 2**32):
            raise ValueError("The given value is out of the range")
        return super(UInt32, cls).__new__(cls, value)

    @override
    def get_dtype(self) -> str:
        """Provide dtype info for pandas

        Returns
        -------
        str
            dtype identifier
        """

        return "uint32"

    def hex(self) -> str:
        """Returns hex representation

        python `hex()` function does not accept object of subclass
        derived from int.

        Returns
        -------
        str
            Hex string (lower case)
        """

        return f"{self:08x}"


class Int32(int, DtypedDecimal):
    def __new__(cls, value: int | None = None) -> Int32:
        """Create immutable instance

        Parameters
        ----------
        value : int, optional
            Value to set

        Returns
        -------
        Int32
            Wrapped value

        Raises
        ------
        ValueError
            Out of range
        """

        if value is None:
            value = 0
        if not (-(2**31) <= value < 2**31):
            raise ValueError("The given value is out of the range")
        return super(Int32, cls).__new__(cls, value)

    @override
    def get_dtype(self) -> str:
        """Provide dtype info for pandas

        Returns
        -------
        str
            dtype identifier
        """

        return "int32"

    def hex(self) -> str:
        """Returns hex representation

        python `hex()` function does not accept object of subclass
        derived from int.

        Returns
        -------
        str
            Hex string (lower case)
        """

        return f"{self:08x}"


class Float32(float, DtypedDecimal):
    def __new__(cls, value: float | None = None) -> Float32:
        if value is None:
            value = 0.0
        if not (-3.4028235e38 <= value <= 3.4028235e38):
            raise ValueError("The given value is out of the range")
        return super(Float32, cls).__new__(cls, value)

    @override
    def get_dtype(self) -> str:
        """Provide dtype info for pandas

        Returns
        -------
        str
            dtype identifier
        """

        return "float32"


class Float64(float, DtypedDecimal):
    def __new__(cls, value: float | None = None) -> Float64:
        if value is None:
            value = 0.0
        if not (-1.7976931348623157e308 <= value <= 1.7976931348623157e308):
            raise ValueError("The given value is out of the range")
        return super(Float64, cls).__new__(cls, value)

    @override
    def get_dtype(self) -> str:
        """Provide dtype info for pandas

        Returns
        -------
        str
            dtype identifier
        """

        return "float64"


T = TypeVar("T")
"""TypeVar for generics"""


class FixedList(MutableSequence[T]):
    """List with fixed length"""

    def __init__(
        self,
        length: int,
        initial_elements: Iterable[T],
    ):
        """Constructor for the sequence

        Parameters
        ----------
        length : int
            Fixed length
        initial_elements : Iterable[T]
            Initial items in iterable representation

        Raises
        ------
        ValueError
            Invalid length
        """

        if length <= 0:
            raise ValueError("Invalid length")
        if not initial_elements:
            raise ValueError(f"Expected {length} elements, got none")
        if length != sum(1 for e in initial_elements):
            raise ValueError(
                f"Expected {length} elements, got {sum(1 for e in initial_elements)}"
            )
        self.__length = length
        self.items = list(initial_elements)

    @overload
    def __getitem__(self, index: int) -> T:
        ...

    @overload
    def __getitem__(self, index: slice) -> MutableSequence[T]:
        ...

    @override
    def __getitem__(self, index: int | slice) -> Any:
        """Get item(s) with index

        Parameters
        ----------
        index : int | slice
            Index for getting data

        Returns
        -------
        Any
            Item or part of sequence

        Raises
        ------
        IndexError
            Out of range
        """

        match index:
            case int():
                if not (0 <= index < self.__length):
                    raise IndexError(
                        f"Index out of range, expected under {self.__length}"
                    )
            case slice():
                if not (
                    0 <= index.start < self.__length and 0 < index.stop <= self.__length
                ):
                    raise IndexError(
                        f"Index out of range, expected under {self.__length}"
                    )
        return self.items[index]

    @override
    def insert(self, index: int, value: T) -> None:
        """Insert an item for the specific index

        Parameters
        ----------
        index : int
            Index to insert
        value : T
            Value of item to insert

        Raises
        ------
        IndexError
            Out of range
        """

        if not (0 <= index < self.__length):
            raise IndexError(f"Index out of range, expected under {self.__length}")
        self.items[index] = value

    @overload
    def __setitem__(self, index: int, value: T) -> None:
        ...

    @overload
    def __setitem__(self, index: slice, value: Iterable[T]) -> None:
        ...

    @override
    def __setitem__(self, index: int | slice, value: Any) -> None:
        """Set item with index

        Parameters
        ----------
        index : int | slice
            Index to set
        value : Any
            Item or part of sequence to set

        Raises
        ------
        IndexError
            Out of range
        """

        match index:
            case int():
                self.insert(index, value)
            case slice():
                if not (
                    0 <= index.start < self.__length and 0 < index.stop <= self.__length
                ):
                    raise IndexError(
                        f"Index out of range, expected under {self.__length}"
                    )
                for i, v in enumerate(value):
                    self.insert(index.start + i, v)

    @overload
    def __delitem__(self, index: int) -> None:
        ...

    @overload
    def __delitem__(self, index: slice) -> None:
        ...

    @override
    def __delitem__(self, index: int | slice) -> None:
        """Delete item with index

        Parameters
        ----------
        index : int | slice
            Index to delete

        Raises
        ------
        RuntimeError
            FixedList does not support deletion
        """

        raise RuntimeError("FixedList does not support deletion")

    @override
    def __len__(self) -> int:
        """Get length

        Returns
        -------
        int
            Length of items
        """

        return self.__length

    @override
    def append(self, value: T) -> None:
        """Append an item

        Parameters
        ----------
        value : T
            Value of the item to append

        Raises
        ------
        IndexError
            FixedList does not support append()
        """

        raise IndexError("FixedList does not support append()")

    @override
    def extend(self, values: Iterable[T]) -> None:
        """Extend the sequence

        Parameters
        ----------
        values : Iterable[T]
            Sequence to extend

        Raises
        ------
        IndexError
            FixedList does not support extend()
        """

        raise IndexError("FixedList does not support extend()")

    @override
    def pop(self, index: int = -1) -> T:
        """Pop an item

        Parameters
        ----------
        index : int
            Index to pop

        Returns
        -------
        T
            An poped item

        Raises
        ------
        RuntimeError
            FixedList does not support pop()
        """

        raise RuntimeError("FixedList does not support pop()")

    @override
    def remove(self, value: T) -> None:
        """Remove an item

        Parameters
        ----------
        value : T
            Value of item to remove

        Raises
        ------
        RuntimeError
            FixedList does not support remove()
        """

        raise RuntimeError("FixedList does not support remove()")

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        """Override the pydantic schema for serialization

        For JSON, serialize as plain list.
        For dict, serialize as object of subclass derived from MutableSequence.

        Parameters
        ----------
        source_type : Any
            The class we are generating a schema for.
        handler : GetCoreSchemaHandler
            Call into Pydantic's internal schema generation.

        Returns
        -------
        CoreSchema
            A `pydantic-core` `CoreSchema`
        """

        return core_schema.json_or_python_schema(
            json_schema=core_schema.list_schema(),
            python_schema=core_schema.any_schema(),
        )


class FixedTuple(Sequence[T]):
    """Tuple with fixed length"""

    def __init__(self, length: int, elements: Iterable[T]):
        """Constructor for the sequence

        Parameters
        ----------
        length : int
            Fixed length
        elements : Iterable[T]
            Items to contain

        Raises
        ------
        ValueError
            Invalid length
        """

        if length <= 0:
            raise ValueError("Invalid length")
        if not elements:
            raise ValueError(f"Expected {length} elements, got none")
        if length != sum(1 for e in elements):
            raise ValueError(
                f"Expected {length} elements, got {sum(1 for e in elements)}"
            )
        self.__length = length
        self.items = tuple(elements)

    @overload
    def __getitem__(self, index: int) -> T:
        ...

    @overload
    def __getitem__(self, index: slice) -> MutableSequence[T]:
        ...

    @override
    def __getitem__(self, index: int | slice) -> Any:
        """Get item(s) with index

        Parameters
        ----------
        index : int | slice
            Index for getting data

        Returns
        -------
        Any
            Item or part of sequence to get
        """

        match index:
            case int():
                if not (0 <= index < self.__length):
                    raise IndexError(
                        f"Index out of range, expected under {self.__length}"
                    )
            case slice():
                if not (
                    0 <= index.start < self.__length and 0 < index.stop <= self.__length
                ):
                    raise IndexError(
                        f"Index out of range, expected under {self.__length}"
                    )
        return self.items[index]

    @override
    def __len__(self) -> int:
        """Get length

        Returns
        -------
        int
            Length for items
        """

        return self.__length

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        """Override the pydantic schema for serialization

        For JSON, serialize as plain tuple.
        For dict, serialize as object of subclass derived from Sequence.

        Parameters
        ----------
        source_type : Any
            The class we are generating a schema for.
        handler : GetCoreSchemaHandler
            Call into Pydantic's internal schema generation.

        Returns
        -------
        CoreSchema
            A `pydantic-core` `CoreSchema`
        """

        return core_schema.json_or_python_schema(
            json_schema=core_schema.tuple_variable_schema(),
            python_schema=core_schema.any_schema(),
        )


class CrossSectional(FixedTuple[T]):
    """Tuple for cross-sectional data such as ADC voltages"""

    pass


class TimeSeries(FixedTuple[T]):
    """Tuple for time series data such as acceleration samples"""

    pass


@final
class PacketType(StrEnum):
    """Packet type identifier for receiving handlers

    Attributes
    ----------
    BARE: str
        Identifier for bare packets
    ACT: str
        Identifier for act packets
    APP_TWELITE: str
        Identifier for App_Twelite packets
    APP_IO: str
        Identifier for App_IO packets
    APP_ARIA: str
        Identifier for App_ARIA packets
    APP_CUE: str
        Identifier for App_CUE packets
    APP_CUE_PAL_EVENT: str
        Identifier for App_CUE (PAL Move or Dice mode) packets
    APP_PAL_OPENCLOSE: str
        Identifier for App_PAL (OPENCLOSE) packets
    APP_PAL_AMB: str
        Identifier for App_PAL (AMB) packets
    APP_PAL_MOT: str
        Identifier for App_PAL (MOT) packets
    APP_UART_ASCII: str
        Identifier for App_Uart (Mode A) packets
    APP_UART_ASCII_EXTENDED: str
        Identifier for App_Uart (Mode A, Extended) packets
    """

    BARE = auto()
    ACT = auto()
    APP_TWELITE = auto()
    APP_IO = auto()
    APP_ARIA = auto()
    APP_CUE = auto()
    APP_CUE_PAL_EVENT = auto()
    APP_PAL_OPENCLOSE = auto()
    APP_PAL_AMB = auto()
    APP_PAL_MOT = auto()
    APP_UART_ASCII = auto()
    APP_UART_ASCII_EXTENDED = auto()


@final
class MagnetState(IntEnum):
    """Event ID for state of the magnet sensor

    For App_ARIA, App_CUE and App_PAL(OPENCLOSE)

    Attributes
    ----------
    NOT_DETECTED: int
        No magnet
    N_POLE_IS_CLOSE: int
        N pole is close
    S_POLE_IS_CLOSE: int
        S pole is close
    """

    NOT_DETECTED = 0x00
    N_POLE_IS_CLOSE = 0x01
    S_POLE_IS_CLOSE = 0x02


@final
class AccelEvent(IntEnum):
    """Event ID for state of the magnet sensor

    Attributes
    ----------
    DICE_1: int
        Dice roll: 1
    DICE_2: int
        Dice roll: 2
    DICE_3: int
        Dice roll: 3
    DICE_4: int
        Dice roll: 4
    DICE_5: int
        Dice roll: 5
    DICE_6: int
        Dice roll: 6
    SHAKE: int
        Shake
    MOVE: int
        Move
    NONE: int
        No events
    """

    DICE_1 = 0x01
    DICE_2 = 0x02
    DICE_3 = 0x03
    DICE_4 = 0x04
    DICE_5 = 0x05
    DICE_6 = 0x06
    SHAKE = 0x08
    MOVE = 0x10
    NONE = 0xFF


@final
class AppPalNoticeColor(IntEnum):
    """Color ID for App_PAL (NOTICE)

    Attributes
    ----------
    RED : int
        RED color
    GREEN : int
        GREEN color
    BLUE : int
        BLUE color
    YELLOW : int
        YELLOW color
    PURPLE : int
        PURPLE color
    LIGHT_BLUE : int
        LIGHT_BLUE color
    WHITE : int
        WHITE color
    WARM_WHITE : int
        WARM_WHITE color
    """

    RED = 0
    GREEN = 1
    BLUE = 2
    YELLOW = 3
    PURPLE = 4
    LIGHT_BLUE = 5
    WHITE = 6
    WARM_WHITE = 7


@final
class AppPalNoticeBlinkSpeed(IntEnum):
    """Blinking speed ID for App_PAL (NOTICE)

    Attributes
    ----------
    ALWAYS_ON : int
        Always on
    SLOW : int
        Slow blinking
    MEDIUM : int
        Medium blinking
    FAST : int
        Fast blinking
    """

    ALWAYS_ON = 0
    SLOW = 1
    MEDIUM = 2
    FAST = 3


@final
class AppPalNoticeRGBWColor(BaseModel):
    """Color in RGBW for App_PAL (NOTICE)

    Attributes
    ----------
    red : UInt8
        Red value 0-0xF
    green : UInt8
        Green value 0-0xF
    blue : UInt8
        Blue value 0-0xF
    white : UInt8
        White value 0-0xF
    """

    red: UInt8 = Field(default=UInt8(0), ge=UInt8(0), le=UInt8(0xF))
    green: UInt8 = Field(default=UInt8(0), ge=UInt8(0), le=UInt8(0xF))
    blue: UInt8 = Field(default=UInt8(0), ge=UInt8(0), le=UInt8(0xF))
    white: UInt8 = Field(default=UInt8(0xF), ge=UInt8(0), le=UInt8(0xF))

    def u16(self) -> UInt16:
        """Returns UInt16 representation

        Returns
        -------
        UInt16
            RGBW as UInt16
        """

        return UInt16(
            (self.white & 0xF) << 12
            | (self.blue & 0xF) << 8
            | (self.green & 0xF) << 4
            | (self.red & 0xF) << 0
        )


@final
class BarePacket(BaseModel):
    """Bare packet dataclass

    Attributes
    ----------
    payload: bytes
        Data payload
    checksum: UInt8
        LRC checksum for data payload
    """

    payload: bytes
    checksum: UInt8

    def __init__(
        self,
        payload: bytes,
        checksum: UInt8 | None = None,
        logical_and_command_id: tuple[UInt8, UInt8] | None = None,
    ):
        """Overridden constructor

        Parameters
        ----------
        payload : bytes
            Payload data
        checksum : UInt8, optional
            LRC8 checksum
        logical_and_command_id : tuple[UInt8, UInt8], optional
            Logical ID and Command ID (if set, payload should be
            shorter
        """

        if logical_and_command_id is not None:
            full_payload_data = bytearray(payload)
            full_payload_data[0:0] = bytes(logical_and_command_id)
            full_payload = bytes(full_payload_data)
            if checksum is not None:
                super().__init__(payload=full_payload, checksum=checksum)
            else:
                super().__init__(
                    payload=full_payload, checksum=utils.lrc8(full_payload)
                )
        else:
            if checksum is not None:
                super().__init__(payload=payload, checksum=checksum)
            else:
                super().__init__(payload=payload, checksum=utils.lrc8(payload))

    def u8_from(self, index: int) -> bytes | None:
        """Get bytes from the specified position in the payload

        Parameters
        ----------
        index : int
            Position index

        Returns
        -------
        bytes | None
            return data if valid else None
        """
        return bytes(self.payload[index:]) if index < len(self.payload) else None

    def u8_at(self, index: int) -> UInt8:
        """Get 1 byte as an unsigned integer for the specified position in the payload

        Parameters
        ----------
        index : int
            Position index

        Returns
        -------
        UInt8
            return data if valid else zero
        """
        return UInt8(self.payload[index] if index < len(self.payload) else 0)

    def i8_at(self, index: int) -> Int8:
        """Get 1 byte as a signed integer for the specified position in the payload

        Parameters
        ----------
        index : int
            Position index

        Returns
        -------
        Int8
            return data if valid else zero
        """
        return Int8(
            int(unpack(">b", self.payload[index : index + 1])[0])
            if index < len(self.payload)
            else 0
        )

    def u16_at(self, index: int) -> UInt16:
        """Get 2 bytes as an unsigned integer for the specified position in the payload

        Parameters
        ----------
        index : int
            Position index

        Returns
        -------
        UInt16
            return data if valid else zero
        """
        return UInt16(
            int(unpack(">H", self.payload[index : index + 2])[0])
            if index + 1 < len(self.payload)
            else 0
        )

    def i16_at(self, index: int) -> Int16:
        """Get 2 bytes as an signed integer for the specified position in the payload

        Parameters
        ----------
        index : int
            Position index

        Returns
        -------
        Int16
            return data if valid else zero
        """
        return Int16(
            int(unpack(">h", self.payload[index : index + 2])[0])
            if index + 1 < len(self.payload)
            else 0
        )

    def u32_at(self, index: int) -> UInt32:
        """Get 4 bytes as an unsigned integer for the specified position in the payload

        Parameters
        ----------
        index : int
            Position index

        Returns
        -------
        UInt32
            return data if valid else zero
        """
        return UInt32(
            int(unpack(">I", self.payload[index : index + 4])[0])
            if index + 3 < len(self.payload)
            else 0
        )

    def i32_at(self, index: int) -> Int32:
        """Get 4 bytes as an signed integer for the specified position in the payload

        Parameters
        ----------
        index : int
            Position index

        Returns
        -------
        Int32
            return data if valid else zero
        """
        return Int32(
            int(unpack(">i", self.payload[index : index + 4])[0])
            if index + 3 < len(self.payload)
            else 0
        )


class ParsedPacketBase(ABC, BaseModel):
    """Base dataclass for data of parsed packets

    Attributes
    ----------
    mwings_implementation: str
        Implementation of mwings; In this case: "python"
    mwings_version: str
        Version of mwings in PEP440 format declared in the pyproject.toml
    time_parsed: str | None
        Date and time parsed in ISO 8601 format
    hostname: str
        Hostname for the running system
    system_type: str
        System type for the running system (e.g. "Linux")
    packet_type: PacketType
        Type of the received packet
    sequence_number: UInt16
        Sequence number for the packet
    source_serial_id: UInt32
        Serial ID for the source device
    source_logical_id: UInt8
        Logical ID for the source device
    lqi: UInt8
        Link quality indicator for the source device (Max: 255)
    supply_voltage: UInt16
        Supply voltage for the source device in mV

    Notes
    -----
    Immutable (frozen) object
    """

    model_config = ConfigDict(frozen=True)

    time_parsed: AwareDatetime | None = Field(default=None)

    packet_type: PacketType = Field(default=PacketType.BARE)
    sequence_number: UInt16 | None = Field(default=None, ge=0, le=0xFFFF)
    source_serial_id: UInt32 = Field(
        default=UInt32(0), ge=UInt32(0), le=UInt32(0xFFFFFFFF)
    )
    source_logical_id: UInt8 = Field(default=UInt8(0))
    lqi: UInt8 | None = Field(default=None, ge=UInt8(0), le=UInt8(255))
    supply_voltage: UInt16 | None = Field(default=None, ge=UInt16(0), le=UInt16(0xFFFF))

    @computed_field
    def mwings_implementation(self) -> str:
        return "python"

    @computed_field
    def mwings_version(self) -> str:
        return metadata.version(__name__.split(".")[0])

    @computed_field
    def hostname(self) -> str:
        return platform.node()

    @computed_field
    def system_type(self) -> str:
        return platform.system()

    @field_validator("time_parsed")
    @classmethod
    def datetime_must_be_clear(cls, dt: datetime | None) -> datetime | None:
        """Check time received

        Must be aware timezone as mw.common.Timezone

        Parameters
        ----------
        dt : datetime
            Input

        Returns
        -------
        datetime
            Valid input

        Raises
        ------
        ValueError
            Native or not same as mw.common.Timezone
        """

        if dt is not None and dt.tzinfo is not Timezone:
            raise ValueError("datetime must be aware and same as mw.common.Timezone.")
        return dt

    @field_validator("source_logical_id")
    @classmethod
    def check_source_logical_id(cls, lid: UInt8) -> UInt8:
        """Check source logical id

        Must be in range between 0 and 100 or 120 and 127

        Parameters
        ----------
        lid : UInt8
            Input

        Returns
        -------
        UInt8
            Valid input

        Raises
        ------
        ValueError
            Out of range
        """

        if 0 <= lid <= 100:
            return lid
        elif lid in range(120, 128):
            return lid
        elif lid in (0xFE, 0xFF):
            return lid
        else:
            raise ValueError("must be in range (0-100) or (120-127)")

    @field_serializer("time_parsed")
    def serialize_time_parsed(self, dt: datetime | None) -> str | None:
        """Print time_parsed in ISO 8601 format

        Parameters
        ----------
        dt : datetime, optional
            Date and time received

        Returns
        -------
        str | None
            Serialized text for JSON or something

        Notes
        -----
        Date and time should be UTC, but python uses "+00:00" suffix instead of "Z".
        However, it can be parsed in other environments like ECMAScript's Date().
        """
        if dt is None:
            return None
        return dt.isoformat()  # YYYY-MM-DDThh:mm:ss.ssssss+00:00

    @field_serializer("packet_type")
    def serialize_packet_type(self, packet_type: PacketType) -> str:
        """Print packet_type in readable names for JSON or something

        Parameters
        ----------
        packet_type : PacketType
            Type of the packet

        Returns
        -------
        str
            Serialized text for JSON or something
        """
        return packet_type.name

    @field_serializer("source_serial_id")
    def serialize_source_serial_id(self, source_serial_id: UInt32) -> str:
        """Print source_serial_id in HEX for JSON or something

        Parameters
        ----------
        source_serial_id : UInt32
            Source serial ID

        Returns
        -------
        str
            Serialized text for JSON or something
        """

        return source_serial_id.hex().upper()

    def to_dict(
        self,
        include: set[str] | None = None,
        exclude: set[str] | None = None,
        verbose: bool = True,
        spread: bool = False,
        sort_keys: bool = False,
    ) -> dict[str, Any]:
        """Export to a dictionary (or OrderedDict)

        Parameters
        ----------
        include : set[str], optional
            Properties to include in the dictionary
        exclude : set[str], optional
            Properties to exclude in the dictionary
        verbose : bool
            Set False to exclude system information.
            Only valid if include and exclude are None.
        spread : bool
            Spread cross-sectional tuple values into separated properties if True
        sort_keys : bool
            Returns a sorted OrderedDict if True

        Returns
        -------
        dict[str, Any]
            Output dictionary (or OrderedDict)

        Notes
        -----
        Higher-level implementation of pydantic's model_dump()
        """

        if not spread:
            if not sort_keys:
                if not verbose and not any((include, exclude)):
                    return self.model_dump(
                        exclude={
                            "mwings_implementation",
                            "mwings_version",
                            "system_type",
                            "hostname",
                        }
                    )
                else:
                    return self.model_dump(include=include, exclude=exclude)
            else:
                return OrderedDict(
                    sorted(
                        self.to_dict(
                            include=include, exclude=exclude, verbose=verbose
                        ).items()
                    )
                )
        else:
            ordered_dict = OrderedDict()
            for key, value in self.to_dict(
                include=include, exclude=exclude, verbose=verbose, sort_keys=sort_keys
            ).items():
                if isinstance(value, CrossSectional):
                    for tup_index, tup_elem in enumerate(value):
                        ordered_dict[f"{key}_{tup_index+1}"] = tup_elem
                else:
                    ordered_dict[key] = value
            return ordered_dict if sort_keys else dict(ordered_dict)

    def to_json(
        self,
        include: set[str] | None = None,
        exclude: set[str] | None = None,
        verbose: bool = True,
        spread: bool = False,
        indent: int | None = 2,
        sort_keys: bool = False,
    ) -> str:
        """Export to a JSON string

        Parameters
        ----------
        include : set[str], optional
            Properties to include the JSON
        exclude : set[str], optional
            Properties to exclude the JSON
        verbose : bool
            Set False to exclude system information.
            Only valid if include and exclude are None.
        spread : bool
            Spread cross-sectional tuple values into separated properties if True
        indent : int, optional
            Space-indentation width (default: 2, None to single-line)
        sort_keys : bool
            Sort properties by keys if True

        Returns
        -------
        str
            Output JSON
        """

        dic = self.to_dict(
            include=include,
            exclude=exclude,
            verbose=verbose,
            spread=spread,
            sort_keys=sort_keys,
        )
        for key, value in dic.items():
            if isinstance(value, FixedTuple):
                dic[key] = tuple(value)  # Make serializable
        return dumps(dic, indent=indent)

    def to_df(
        self,
        include: set[str] | None = None,
        exclude: set[str] | None = None,
        verbose: bool = True,
    ) -> pd.DataFrame:
        """Export to a pandas DataFrame

        Requires optional dependency: pandas

        Parameters
        ----------
        include : set[str], optional
            Columns to include in the DataFrame
        exclude : set[str], optional
            Columns to include in the DataFrame
        verbose : bool
            Set False to exclude system information.
            Only valid if include and exclude are None.

        Returns
        -------
        pd.DataFrame
            Output DataFrame

        Raises
        ------
        EnvironmentError
            No pandas found
        """

        if PANDAS_AVAILABLE:
            dic = self.to_dict(
                include=include,
                exclude=exclude,
                verbose=verbose,
                spread=True,
            )
            df = pd.DataFrame()
            time_series_max = max(
                [
                    len(value) if isinstance(value, TimeSeries) else 0
                    for value in dic.values()
                ]
            )
            if time_series_max == 0:
                for key in dic:
                    df[key] = [dic[key]]
                    match dic[key]:
                        case DtypedDecimal():
                            df[key] = df[key].astype(dic[key].get_dtype())
                        case str():
                            df[key] = df[key].astype("string")
                df.insert(1, "time_series", [0])
            else:
                for key in dic:
                    if isinstance(dic[key], TimeSeries):
                        df[key] = [
                            dic[key][i] if dic[key][i] else type(dic[key][0])()
                            for i in range(time_series_max)
                        ]
                        match dic[key][0]:
                            case DtypedDecimal():
                                df[key] = df[key].astype(dic[key][0].get_dtype())
                            case str():
                                df[key] = df[key].astype("string")
                    else:
                        df[key] = [dic[key] for _ in range(time_series_max)]
                        match dic[key]:
                            case DtypedDecimal():
                                df[key] = df[key].astype(dic[key].get_dtype())
                            case str():
                                df[key] = df[key].astype("string")
                df.insert(1, "time_series", range(time_series_max))
            df["time_series"] = df["time_series"].astype("uint8")
            df["time_parsed"] = df["time_parsed"].apply(
                pd.to_datetime, utc=Timezone is timezone.utc, format="ISO8601"
            )
            return df
        else:
            raise EnvironmentError("to_df() requires pandas")


SomeParsedPacket = TypeVar("SomeParsedPacket", bound=ParsedPacketBase)
"""TypeVar for all classes derived from ParsedPacketBase"""


class CommandBase(ABC, BaseModel):
    """Base dataclass for commands

    Attributes
    ----------
    destination_logical_id: UInt8
        Logical ID for the source device
    """

    model_config = ConfigDict()

    destination_logical_id: UInt8 = Field(default=UInt8(0x78))

    @abstractmethod
    def is_valid(self) -> bool:
        """Check if the command content is valid or not

        Returns
        -------
        bool
            True if valid

        Notes
        -----
        Pure virtual function
        """
        pass


class PacketParserBase(ABC):
    """Base class for packet parsers"""

    @staticmethod
    @abstractmethod
    def is_valid(bare_packet: BarePacket) -> bool:
        """Check if the given bare packet is valid or not

        Parameters
        ----------
        bare_packet : BarePacket
            Bare packet content

        Returns
        -------
        bool
            True if valid

        Notes
        -----
        Pure virtual function
        """
        pass

    @staticmethod
    @abstractmethod
    def parse(bare_packet: BarePacket) -> ParsedPacketBase | None:
        """Parse the given bare packet

        Parameters
        ----------
        bare_packet : BarePacket
            Bare packet content

        Returns
        -------
        ParsedPacketBase | None
            Parsed packet content if valid otherwise None

        Notes
        -----
        Pure virtual function
        """
        pass


SomeCommand = TypeVar("SomeCommand", bound=CommandBase)
"""TypeVar for all classes derived from CommandBase"""


class CommandSerializerBase(ABC):
    """Base class for packet serializers"""

    @staticmethod
    @abstractmethod
    def serialize(command: SomeCommand) -> BarePacket | None:
        """Serialize the given command

        Parameters
        ----------
        command : SomeCommand
            Some command to serialize

        Returns
        -------
        BarePacket | None
            Serialized bytes and its LRC checksum (8bit) if valid
        """
        pass
