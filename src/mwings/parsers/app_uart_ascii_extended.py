# -*- coding:utf-8 -*-
# Written for Python 3.12
# Formatted with Black

# Packet parser for App_Uart (Mode A, Extended)

from datetime import datetime
from base64 import b64encode
from typing import Any, final

from overrides import override
from pydantic import Field, computed_field, field_validator

from .. import common


class ParsedPacket(common.ParsedPacketBase):
    """Dataclass for parsed packets from App_Uart (Mode A, Extended)

    Attributes
    ----------
    destination_serial_id: common.UInt32
        Serial ID for the destination (parent) device
    command_id: common.UInt8
        Command ID
    data: bytes
        Data body (Hidden in JSON or something)
    data_base64: str
        Data body in Base64 for JSON or something
    data_hexstr: str
        Data body in ASCII string
    """

    destination_serial_id: common.UInt32 = Field(
        default=common.UInt32(0x78), ge=common.UInt32(0), le=common.UInt32(0xFFFFFFFF)
    )
    command_id: common.UInt8 = Field(
        default=common.UInt8(0x00), ge=common.UInt8(0), lt=common.UInt8(0x80)
    )
    data: bytes = Field(default=bytes(), exclude=True)

    @computed_field
    def data_base64(self) -> str:
        return b64encode(self.data).decode("ascii")

    @computed_field
    def data_hexstr(self) -> str:
        return self.data.hex().upper()

    @field_validator("data")
    @classmethod
    def check_data(cls, data: bytes) -> bytes:
        """Check for data

        Parameters
        ----------
        data : bytes
            Input

        Returns
        -------
        bytes
            Valid input

        Raises
        ------
        ValueError
            Byte length is not in range between 1 and 80
        """

        if not (1 <= len(data) <= 80):
            raise ValueError("Payload length should be in range between 1 and 80.")
        return data


class PacketParser(common.PacketParserBase):
    """Packet parser for App_Uart (Mode A, Extended)"""

    @staticmethod
    @final
    @override
    def is_valid(bare_packet: common.BarePacket) -> bool:
        """Check the given bare packet is valid or not

        Parameters
        ----------
        bare_packet : common.BarePacket
            Bare packet content

        Returns
        -------
        bool
            True if valid

        Notes
        -----
        Static overridden method
        """
        if (
            (0x00 <= bare_packet.u8_at(0) <= 0x64 or bare_packet.u8_at(0) == 0x78)
            and bare_packet.u8_at(1) == 0xA0
            and bare_packet.u8_at(2) < 0x80
            and (bare_packet.u8_at(3) & 0x80) == 0x80
            and bare_packet.u16_at(12) == len(bare_packet.payload) - 14
        ):
            return True
        return False

    @staticmethod
    @final
    @override
    def parse(bare_packet: common.BarePacket) -> ParsedPacket | None:
        """Try to parse the given bare packet

        Parameters
        ----------
        bare_packet : common.BarePacket
            Bare packet content

        Returns
        -------
        ParsedPacket | None
            Parsed packet data if valid else None

        Notes
        -----
        Static overridden method
        """
        if not PacketParser.is_valid(bare_packet):
            return None
        parsed_packet_data: dict[str, Any] = {
            "time_parsed": datetime.now(common.Timezone),
            "packet_type": common.PacketType.APP_UART_ASCII_EXTENDED,
            "sequence_number": None,
            "source_serial_id": bare_packet.u32_at(3),
            "source_logical_id": bare_packet.u8_at(0),
            "lqi": bare_packet.u8_at(11),
            "supply_voltage": None,
            "destination_serial_id": bare_packet.u32_at(7),
            "command_id": bare_packet.u8_at(2),
            "data": bare_packet.u8_from(14),
        }
        return ParsedPacket(**parsed_packet_data)
