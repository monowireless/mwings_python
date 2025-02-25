# -*- coding:utf-8 -*-
# Written for Python 3.12
# Formatted with Black

# MWings

from enum import IntEnum, auto
from threading import Thread, Event
from datetime import timezone, tzinfo
from typing import Any, Callable, Self, overload, final
from types import TracebackType
from warnings import warn

import serial  # type: ignore
from pyee.base import EventEmitter
from overrides import override

from . import common
from . import utils
from . import parsers
from . import serializers


@final
class Twelite(Thread):
    """MWings main class"""

    # Private inner enum classes
    @final
    class __State(IntEnum):
        """Parser state

        Attributes
        ----------
        WAITING_FOR_HEADER: int
            Waiting for the header character ':'
        RETRIEVING_PAYLOAD: int
            Retrieving packet payload data
        WAITING_FOR_FOOTER: int
            Waiting for the footer character <LF>
        COMPLETED: int
            Completed to receive a packet
        CHECKSUM_ERROR: int
            Error in checksum
        UNKNOWN_ERROR: int
            Unknown error
        """

        WAITING_FOR_HEADER = auto()
        RETRIEVING_PAYLOAD = auto()
        WAITING_FOR_FOOTER = auto()
        COMPLETED = auto()
        UNKNOWN_ERROR = auto()
        CHECKSUM_ERROR = auto()
        TIMEOUT_ERROR = auto()

    @final
    class __Command(IntEnum):
        """Revised 0xDB commands

        Attributes
        ----------
        ACK: int
            Revised 0xDB command: Ack
        MODULE_ADDRESS: int
            Revised 0xDB command: Module address
        SET_PARAMETER: int
            Revised 0xDB command: Set parameter
        GET_PARAMETER: int
            Revised 0xDB command: Get parameter
        CONTROL: int
            Revised 0xDB command: Control module
        DISABLE_SILENT_MODE: int
            Revised 0xDB command: Disable silent mode
        CLEAR: int
            Revised 0xDB command: Clear settings
        SAVE: int
            Revised 0xDB command: Save settings
        RESET: int
            Revised 0xDB command: Reset module
        """

        ACK = 0xD0
        MODULE_ADDRESS = 0xD1
        SET_PARAMETER = 0xD2
        GET_PARAMETER = 0xD3
        CONTROL = 0xD8
        DISABLE_SILENT_MODE = 0xD9
        CLEAR = 0xDD
        SAVE = 0xDE
        RESET = 0xDF

    @final
    class __Parameter(IntEnum):
        """Parameter for commands: set/get parameter

        Attributes
        ---------
        APP_ID: int
            Application ID
        CH_MASK: int
            Channels bit mask
        RETRY_TX: int
            Retry count / Tx power
        ROUTING_LAYER: int
            Routing layer
        AP_ADDRESS: int
            Access point address
        UART_BAUDRATE: int
            Uart baudrate
        ENCRYPTION: int
            Encryption settings
        OPTION_BITS: int
            Option bits
        """

        APP_ID = 0x01
        CH_MASK = 0x02
        RETRY_TX = 0x03
        ROUTING_LAYER = 0x04
        AP_ADDRESS = 0x05
        UART_BAUDRATE = 0x06
        ENCRYPTION = 0x07
        OPTION_BITS = 0x08

    @final
    class __SavingStatus(IntEnum):
        """Return status during saving parameters

        Attributes
        ----------
        SUCCEEDED: int
            Succeeded
        FAILED: int
            Failed
        SUCCEEDED_NO_MODIFICATIONS: int
            Succeeded, but no modifications
        FAILED_NO_MODIFICATIONS: int
            Failed, but no modifications
        """

        SUCCEEDED = 0x01
        FAILED = 0x00
        SUCCEEDED_NO_MODIFICATIONS = 0x81
        FAILED_NO_MODIFICATIONS = 0x80

    # Private varibles

    # pyserial instance
    __serial: serial.Serial | None = None

    # Rx binary data buffer
    __buffer: bytearray

    # Max size of the rx buffer
    __rx_buffer_size: int

    # Number of received ASCII characters
    __character_count: int

    # LRC checksum for the latest received packet
    __checksum: int

    # Timeout for each packet in milliseconds
    __timeout: int

    # Timestamp of the last time the header was received
    __latest_timestamp: int

    # Print debug info if True
    __debugging: bool

    # Parser state
    __state: __State

    # Event emitter for receiving events
    __event_emitter: EventEmitter

    # Status for the receiver thread
    __running: bool

    # Set to ensure the receiver thread has stopped
    __ensure_stopped: Event

    # Public methods

    def __init__(
        self,
        port: str | None = None,
        rx_buffer_size: int = 1024,
        timeout: int = 100,
        tz: tzinfo | None = None,
        debugging: bool = False,
    ):
        """Constructor

        Parameters
        ----------
        port : str | None
            Name for the serial port to use / set None to disable serial
        rx_buffer_size : int
            Receive buffer size
        timeout : int
            Timeout for each packet in milliseconds
        tz : tzinfo
            Timezone for datetime data. Default is UTC (Aware). Use ZoneInfo() for others.
        debugging : bool
            Print debug info if true
        """

        super().__init__()
        self.daemon = False

        if port is not None:
            try:
                self.__serial = serial.Serial(port, 115200, timeout=1)
            except serial.serialutil.SerialException:
                raise IOError("Specified port is busy or not available")

        self.__buffer = bytearray()
        self.__rx_buffer_size = rx_buffer_size
        self.__character_count = 0
        self.__checksum = 0
        self.__timeout = timeout
        self.__latest_timestamp = -1
        self.__debugging = debugging
        self.__state = self.__State.WAITING_FOR_HEADER
        self.__event_emitter = EventEmitter()
        self.__running = False
        self.__ensure_stopped = Event()
        common.Timezone = tz if tz is not None else timezone.utc

    def __del__(self) -> None:
        """Destructor"""
        self.close()

    def __enter__(self) -> Self:
        """Enter the runtime context related to this object."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        """Exit the runtime context and close the connection."""
        self.close()
        return None

    def close(self) -> None:
        """Close the serial port if opened"""
        if self.__serial is not None:
            if self.__running:
                self.stop()
            if self.__serial.is_open:
                self.__serial.close()

    def clear_input(self) -> None:
        """Clear input buffer of serial and packets"""
        if self.__serial is not None and self.__serial.is_open:
            self.__serial.reset_input_buffer()
        self.__buffer.clear()

    @staticmethod
    def set_timezone(tz: tzinfo | None) -> None:
        """Set timezone for received data

        Parameters
        ----------
        tz : tzinfo
            tzinfo object. Typically Zoneinfo("IANA/City"). None for UTC.
        """

        common.Timezone = tz if tz is not None else timezone.utc

    @property
    def timezone(self) -> tzinfo:
        """Get timezone set

        Returns
        -------
        tzinfo
            Timezone set for mwings
        """

        return common.Timezone

    @overload
    def add_listener(
        self, event: common.PacketType, handler: Callable[[common.BarePacket], None]
    ) -> None:
        """Register a handler for receiving packets

        Parameters
        ----------
        event : common.PacketType
            Identifier for packets to receive
        handler : Callable[[common.BarePacket], None]
            Handler to handle bare packets
        """
        ...

    @overload
    def add_listener(
        self,
        event: common.PacketType,
        handler: Callable[[common.SomeParsedPacket], None],
    ) -> None:
        """Register a handler for receiving packets

        Parameters
        ----------
        event : common.PacketType
            Identifier for packets to receive
        handler : Callable[[common.SomeParsedPacket], None]
            Handler to handle some parsed packets
        """
        ...

    def add_listener(
        self, event: common.PacketType, handler: common.SomeCallable
    ) -> None:
        """Register a handler for receiving packets

        Parameters
        ----------
        event : common.PacketType
            Identifier for packets to receive
        handler : common.SomeCallable
            Handler to handle packets
        """

        self.__event_emitter.add_listener(event, handler)

    def remove_all_listeners(self, event: common.PacketType | None) -> None:
        """Remove all handlers for receicing packets

        Parameters
        ----------
        event : common.PacketType
            Identifier for packets to receive
        """

        self.__event_emitter.remove_all_listeners(event)

    def on(
        self, event: common.PacketType
    ) -> Callable[[common.SomeCallable], common.SomeCallable]:
        """Generate a decorator to register a handler for receiving packets

        Parameters
        ----------
        event : common.PacketType
            Identifier for packets to receive

        Returns
        -------
        Callable[[common.SomeCallable], common.SomeCallable]
            Decorator to register a handler for receiving packets
        """

        def decorator(handler: common.SomeCallable) -> common.SomeCallable:
            """Decorator to register a handler for receiving packets

            Parameters
            ----------
            handler : common.SomeCallable
                Original handler for receiving packets

            Returns
            -------
            common.SomeCallable
                Decorated handler for receiving packets (Actually, it's same)
            """

            self.add_listener(event, handler)
            return handler

        return decorator

    @overload
    def send(self, data: common.BarePacket) -> bool:
        """Send data to the device with ModBus format

        Parameters
        ----------
        data : common.BarePacket
            Payload and checksum data to send

        Returns
        -------
        bool
            True if succeeded
        """
        ...

    @overload
    def send(self, data: common.SomeCommand) -> bool:
        """Send data to the device with ModBus format

        Parameters
        ----------
        data : common.SomeCommand
            Some command to serialize and send

        Returns
        -------
        bool
            True if succeeded
        """
        ...

    def send(self, data: Any) -> bool:
        """Send data to the device with ModBus format

        Parameters
        ----------
        data : Any
            Data to send

        Returns
        -------
        bool
            True if succeeded
        """

        if self.__serial is None:
            raise RuntimeError("send() can only be used when the port is initialized")

        if not utils.is_writable(self.__serial):
            return False

        match data:
            case common.BarePacket():
                utils.write_binary(self.__serial, ord(":"))
                utils.write_in_ascii(self.__serial, data.payload)
                utils.write_in_ascii(self.__serial, data.checksum)
                utils.write_binary(self.__serial, ord("\r"))
                utils.write_binary(self.__serial, ord("\n"))
                if self.__debugging:
                    print(f"Sent ascii: {data.payload.hex()}")
            case serializers.app_twelite.Command():
                serialized_data = serializers.app_twelite.CommandSerializer.serialize(
                    data
                )
                if serialized_data is None:
                    return False
                else:
                    self.send(serialized_data)
            case serializers.app_io.Command():
                serialized_data = serializers.app_io.CommandSerializer.serialize(data)
                if serialized_data is None:
                    return False
                else:
                    self.send(serialized_data)
            case serializers.app_pal_notice.Command():
                serialized_data = (
                    serializers.app_pal_notice.CommandSerializer.serialize(data)
                )
                if serialized_data is None:
                    return False
                else:
                    self.send(serialized_data)
            case serializers.app_pal_notice_detailed.Command():
                serialized_data = (
                    serializers.app_pal_notice_detailed.CommandSerializer.serialize(
                        data
                    )
                )
                if serialized_data is None:
                    return False
                else:
                    self.send(serialized_data)
            case serializers.app_pal_notice_event.Command():
                serialized_data = (
                    serializers.app_pal_notice_event.CommandSerializer.serialize(data)
                )
                if serialized_data is None:
                    return False
                else:
                    self.send(serialized_data)
            case serializers.app_uart_ascii.Command():
                serialized_data = (
                    serializers.app_uart_ascii.CommandSerializer.serialize(data)
                )
                if serialized_data is None:
                    return False
                else:
                    self.send(serialized_data)
        return True

    @override
    def start(self) -> None:
        """Start the thread to receive continuously

        Notes
        -----
        Overrides threading.Thread.start()
        """

        if self.__serial is None:
            raise RuntimeError("start() can only be used when the port is initialized")

        self.__running = True
        super().start()

    @override
    def run(self) -> None:
        """Run the thread to receive continuously

        Call this function via Twelite.start()

        Notes
        -----
        Overrides threading.Thread.run()
        """

        while self.__running:
            self.update()
        self.__ensure_stopped.set()

    def stop(self) -> None:
        """Stop the thread to receive continuously"""

        if self.__serial is None:
            raise RuntimeError("stop() can only be used when the port is initialized")

        self.__ensure_stopped.clear()
        self.__running = False
        self.__ensure_stopped.wait()

    def receive(self) -> common.PacketType:
        """Wait for parsing of a single packet

        Returns
        -------
        common.PacketType
            Identifier for packet received

        Notes
        -----
        This function blocks current thread
        """

        if self.__serial is None:
            raise RuntimeError(
                "receive() can only be used when the port is initialized"
            )

        while True:
            if (packet_type := self.update()) is not None:
                return packet_type

    def update(self) -> common.PacketType | None:
        """Update parsing state with serial data

        Returns
        -------
        common.PacketType | None
            Returns packet type identifier if available else None
        """

        if self.__serial is None:
            raise RuntimeError("update() can only be used when the port is initialized")

        # Abort if the serial is not initialized
        if not utils.is_initialized(self.__serial):
            return None

        # Process all byte in the buffer
        while utils.is_readable(self.__serial):
            # Parse a read character
            result = self.__parse(int.from_bytes(self.__serial.read()))
            if result is not None:
                # When parsed a complete packet
                return result
        return None

    def parse_line(self, line: str, use_lf: bool = True) -> common.PacketType | None:
        """Parse a single string

        Useful when use local log file instead of serial port rx

        Parameters
        ----------
        line : str
            String line
        use_lf : bool
            Use LF instead of CRLF (For f.readline, set True as
            default)

        Returns
        -------
        common.PacketType | None
            Latest packet type identifier if available else None

        Raises
        ------
        RuntimeError
            Serial IS initialized
        """
        if self.__serial is not None:
            raise RuntimeError(
                "parse_line() can only be used when the port is NOT initialized"
            )
        result: common.PacketType | None = None
        for character in line.lstrip():
            # Parse a read character
            latest_result = self.__parse(character, use_lf)
            if latest_result is not None:
                # When parsed a complete packet
                result = latest_result
        return result

    @overload
    def parse(self, character: str, use_lf: bool = False) -> common.PacketType | None:
        ...

    @overload
    def parse(self, character: bytes, use_lf: bool = False) -> common.PacketType | None:
        ...

    @overload
    def parse(self, character: int, use_lf: bool = False) -> common.PacketType | None:
        ...

    def parse(self, character: Any, use_lf: bool = False) -> common.PacketType | None:
        """Parse a single character

        Parameters
        ----------
        character : Any
            character to parse
        use_lf : bool
            If use LF instead of CRLF, set True

        Returns
        -------
        common.PacketType | None
            If completed, returns packet type identifier

        Raises
        ------
        RuntimeError
            Serial IS initialized
        ValueError
            Unsupported character
        """
        if self.__serial is not None:
            raise RuntimeError(
                "parse() can only be used when the port is NOT initialized"
            )
        return self.__parse(character, use_lf)

    # Private method(s)

    @overload
    def __parse(self, character: str, use_lf: bool = False) -> common.PacketType | None:
        ...

    @overload
    def __parse(
        self, character: bytes, use_lf: bool = False
    ) -> common.PacketType | None:
        ...

    @overload
    def __parse(self, character: int, use_lf: bool = False) -> common.PacketType | None:
        ...

    def __parse(self, character: Any, use_lf: bool = False) -> common.PacketType | None:
        """Parse a single character

        Parameters
        ----------
        character : Any
            character to parse
        use_lf : bool
            If use LF instead of CRLF, set True

        Returns
        -------
        common.PacketType | None
            If completed, returns packet type identifier

        Raises
        ------
        ValueError
            Unsupported character
        """
        match character:
            case str():
                if len(character) != 1:
                    raise ValueError("character must be single length")
                character_bytes: bytes
                try:
                    character_bytes = character.encode("ascii")
                except UnicodeEncodeError:
                    raise ValueError("character must bpe ASCII")
                return self.__parse(character_bytes, use_lf)
            case bytes():
                if len(character) != 1:
                    raise ValueError("character must be single length")
                return self.__parse(character[0], use_lf)
            case int():
                # Abort if the read byte is invalid
                if not (0 <= character <= 0xFF):
                    return None
                if self.__debugging:
                    pass
                    # print(repr(chr(character)))

                # Process packet contents upon parsing completion
                if (bare_packet := self.__process_ascii(character, use_lf)) is not None:
                    # Emit events here

                    # Bare packet handler
                    self.__event_emitter.emit(common.PacketType.BARE, bare_packet)

                    # Act packet handler
                    if parsers.act.PacketParser.is_valid(bare_packet):
                        if (
                            self.__event_emitter.emit(
                                common.PacketType.ACT,
                                parsers.act.PacketParser.parse(bare_packet),
                            )
                            is not True
                            and self.__debugging
                        ):
                            warn(
                                f"No handler(s) registered for {common.PacketType.ACT}"
                            )
                        return common.PacketType.ACT

                    # App_Twelite packet handler
                    if parsers.app_twelite.PacketParser.is_valid(bare_packet):
                        if (
                            self.__event_emitter.emit(
                                common.PacketType.APP_TWELITE,
                                parsers.app_twelite.PacketParser.parse(bare_packet),
                            )
                            is not True
                            and self.__debugging
                        ):
                            warn(
                                f"No handler(s) registered for {common.PacketType.APP_TWELITE}"
                            )
                        return common.PacketType.APP_TWELITE

                    # App_Io packet handler
                    if parsers.app_io.PacketParser.is_valid(bare_packet):
                        if (
                            self.__event_emitter.emit(
                                common.PacketType.APP_IO,
                                parsers.app_io.PacketParser.parse(bare_packet),
                            )
                            is not True
                            and self.__debugging
                        ):
                            warn(
                                f"No handler(s) registered for {common.PacketType.APP_IO}"
                            )
                        return common.PacketType.APP_IO

                    # App_ARIA packet handler
                    if parsers.app_aria.PacketParser.is_valid(bare_packet):
                        if (
                            self.__event_emitter.emit(
                                common.PacketType.APP_ARIA,
                                parsers.app_aria.PacketParser.parse(bare_packet),
                            )
                            is not True
                            and self.__debugging
                        ):
                            warn(
                                f"No handler(s) registered for {common.PacketType.APP_ARIA}"
                            )
                        return common.PacketType.APP_ARIA

                    # App_CUE packet handler
                    if parsers.app_cue.PacketParser.is_valid(bare_packet):
                        if (
                            self.__event_emitter.emit(
                                common.PacketType.APP_CUE,
                                parsers.app_cue.PacketParser.parse(bare_packet),
                            )
                            is not True
                            and self.__debugging
                        ):
                            warn(
                                f"No handler(s) registered for {common.PacketType.APP_CUE}"
                            )
                        return common.PacketType.APP_CUE

                    # App_CUE (PAL Move or Dice mode) packet handler
                    if parsers.app_cue_pal_event.PacketParser.is_valid(bare_packet):
                        if (
                            self.__event_emitter.emit(
                                common.PacketType.APP_CUE_PAL_EVENT,
                                parsers.app_cue_pal_event.PacketParser.parse(
                                    bare_packet
                                ),
                            )
                            is not True
                            and self.__debugging
                        ):
                            warn(
                                f"No handler(s) registered for {common.PacketType.APP_CUE_PAL_EVENT}"
                            )
                        return common.PacketType.APP_CUE_PAL_EVENT

                    # App_PAL (OPENCLOSE) packet handler
                    if parsers.app_pal_openclose.PacketParser.is_valid(bare_packet):
                        if (
                            self.__event_emitter.emit(
                                common.PacketType.APP_PAL_OPENCLOSE,
                                parsers.app_pal_openclose.PacketParser.parse(
                                    bare_packet
                                ),
                            )
                            is not True
                            and self.__debugging
                        ):
                            warn(
                                f"No handler(s) registered for {common.PacketType.APP_PAL_OPENCLOSE}"
                            )
                        return common.PacketType.APP_PAL_OPENCLOSE

                    # App_PAL (AMB) packet handler
                    if parsers.app_pal_amb.PacketParser.is_valid(bare_packet):
                        if (
                            self.__event_emitter.emit(
                                common.PacketType.APP_PAL_AMB,
                                parsers.app_pal_amb.PacketParser.parse(bare_packet),
                            )
                            is not True
                            and self.__debugging
                        ):
                            warn(
                                f"No handler(s) registered for {common.PacketType.APP_PAL_AMB}"
                            )
                        return common.PacketType.APP_PAL_AMB

                    # App_PAL (MOT) packet handler
                    if parsers.app_pal_mot.PacketParser.is_valid(bare_packet):
                        if (
                            self.__event_emitter.emit(
                                common.PacketType.APP_PAL_MOT,
                                parsers.app_pal_mot.PacketParser.parse(bare_packet),
                            )
                            is not True
                            and self.__debugging
                        ):
                            warn(
                                f"No handler(s) registered for {common.PacketType.APP_PAL_MOT}"
                            )
                        return common.PacketType.APP_PAL_MOT

                    # App_Uart (Mode A) packet handler
                    if parsers.app_uart_ascii.PacketParser.is_valid(bare_packet):
                        if (
                            self.__event_emitter.emit(
                                common.PacketType.APP_UART_ASCII,
                                parsers.app_uart_ascii.PacketParser.parse(bare_packet),
                            )
                            is not True
                            and self.__debugging
                        ):
                            warn(
                                f"No handler(s) registered for {common.PacketType.APP_UART_ASCII}"
                            )
                        return common.PacketType.APP_UART_ASCII

                    # App_Uart (Mode A, Extended) packet handler
                    if parsers.app_uart_ascii_extended.PacketParser.is_valid(
                        bare_packet
                    ):
                        if (
                            self.__event_emitter.emit(
                                common.PacketType.APP_UART_ASCII_EXTENDED,
                                parsers.app_uart_ascii_extended.PacketParser.parse(
                                    bare_packet
                                ),
                            )
                            is not True
                            and self.__debugging
                        ):
                            warn(
                                f"No handler(s) registered for {common.PacketType.APP_UART_ASCII_EXTENDED}"
                            )
                        return common.PacketType.APP_UART_ASCII_EXTENDED

                    return common.PacketType.BARE
        return None

    def __process_ascii(
        self, character: int, use_lf: bool = False
    ) -> common.BarePacket | None:
        """Process an ascii character

        Parameters
        ----------
        character : int
            ASCII code for the received character
        use_lf : bool
            If use LF instead of CRLF, set True

        Returns
        -------
        common.BarePacket | None
            Complete bare packet if received the whole packet else None
        """

        # Reset if the state is error or completed
        if (
            self.__state == self.__State.COMPLETED
            or self.__state == self.__State.UNKNOWN_ERROR
            or self.__state == self.__State.CHECKSUM_ERROR
            or self.__state == self.__State.TIMEOUT_ERROR
        ):
            self.__state = self.__State.WAITING_FOR_HEADER

        # Reset on timeout
        if (
            self.__timeout > 0
            and self.__state != self.__State.WAITING_FOR_HEADER
            and utils.millis() - self.__latest_timestamp > self.__timeout
        ):
            self.__state = self.__State.TIMEOUT_ERROR
            if self.__debugging:
                print("TIMEOUT_ERROR\n")

        # Run state machine
        match self.__state:
            case self.__State.WAITING_FOR_HEADER:
                # If the character is colon, start to read
                if character == ord(":"):
                    self.__state = self.__State.RETRIEVING_PAYLOAD
                    self.__latest_timestamp = utils.millis()
                    self.__character_count = 0
                    self.__checksum = 0
                    self.__buffer = bytearray()
            case self.__State.RETRIEVING_PAYLOAD:
                if (character >= ord("0") and character <= ord("9")) or (
                    character >= ord("A") and character <= ord("F")
                ):
                    # Valid hex character

                    # Abort if the buffer is overflowing
                    if (
                        utils.byte_count_from(self.__character_count)
                        >= self.__rx_buffer_size
                    ):
                        self.__state = self.__State.UNKNOWN_ERROR
                        if self.__debugging:
                            print("OVERFLOW ERROR\n")

                    # Convert character to hex
                    hex_value: int = utils.hex_from(character)

                    # Get an index for the new byte
                    newByteIndex: int = (
                        utils.byte_count_from(self.__character_count) + 1 - 1
                    )  # next position, but zero origin

                    # Add byte
                    if self.__character_count & 1:
                        # Odd: set 0-3 bit of the new byte
                        self.__buffer[newByteIndex] = (
                            self.__buffer[newByteIndex] & 0xF0
                        ) | hex_value
                        self.__checksum += self.__buffer[newByteIndex]
                    else:
                        # Even: set 7-4 bit of the byte
                        self.__buffer.append(hex_value << 4)
                    self.__character_count += 1

                elif (not use_lf and character == ord("\r")) or (
                    use_lf and character == ord("\n")
                ):
                    # Abort if received data are not valid
                    if (
                        not self.__character_count >= 4
                        and (self.__character_count & 1) == 0
                    ):
                        self.__state = self.__State.UNKNOWN_ERROR
                        if self.__debugging:
                            print("LENGTH ERROR")

                    # Mask checksum
                    self.__checksum = self.__checksum & 0xFF

                    # Abort if the checksum is not valid
                    if not self.__checksum == 0:
                        self.__state = self.__State.CHECKSUM_ERROR
                        if self.__debugging:
                            print("CHECKSUM_ERROR")

                    if not use_lf:
                        self.__state = self.__State.WAITING_FOR_FOOTER
                    else:
                        self.__state = self.__State.COMPLETED
                else:
                    # Invalid characters
                    self.__state = self.__State.UNKNOWN_ERROR
                    if self.__debugging:
                        print(f"INVALID CHAR ERROR: {repr(chr(character))}")

            case self.__State.WAITING_FOR_FOOTER:
                if character == ord("\n"):
                    # Completed
                    self.__state = self.__State.COMPLETED
                else:
                    # CR only
                    self.__state = self.__State.UNKNOWN_ERROR
                    if self.__debugging:
                        print("NO LF ERROR")
            case _:
                self.__state = self.__State.UNKNOWN_ERROR
                if self.__debugging:
                    print("UNKNOWN ERROR")

        # Make bare packet available when parsing was completed
        if self.__state == self.__State.COMPLETED:
            bare_packet_data: dict[str, Any] = {
                "payload": bytes(self.__buffer[:-1]),  # -1 for checksum
                "checksum": self.__buffer[
                    utils.byte_count_from(self.__character_count) - 1
                ],
            }
            return common.BarePacket(**bare_packet_data)
        return None
