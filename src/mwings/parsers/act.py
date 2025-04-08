# -*- coding:utf-8 -*-
# Written for Python 3.12
# Formatted with Black

# Packet parser for act

from datetime import datetime
from base64 import b64encode
from typing import Any, final

from pydantic import Field, computed_field
from overrides import override

from .. import common


@final
class ParsedPacket(common.ParsedPacketBase):
    """Dataclass for parsed packets from act

    Attributes
    ----------
    command_id: common.UInt8
        Command ID
    data: bytes
        Data body (Hidden in JSON or something)
    data_base64: str
        Data body in Base64 for JSON or something
    data_hexstr: str
        Data body in ASCII string
    """

    command_id: common.UInt8 = Field(
        default=common.UInt8(0x00), ge=common.UInt8(0x00), lt=common.UInt8(0x7F)
    )
    data: bytes = Field(default=bytes(), exclude=True)

    @computed_field
    def data_base64(self) -> str:
        return b64encode(self.data).decode("ascii")

    @computed_field
    def data_hexstr(self) -> str:
        return self.data.hex().upper()


@final
class PacketParser(common.PacketParserBase):
    """Packet parser for act"""

    @staticmethod
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
            bare_packet.u8_at(1) == 0xAA
            and 0x00 <= bare_packet.u8_at(2) <= 0x7F
            and (bare_packet.u8_at(3) & 0x80) == 0x80
            and ((bare_packet.u8_at(7) & 0x80) == 0x80 or bare_packet.u32_at(7) == 0)
            and bare_packet.u16_at(12) == len(bare_packet.payload) - 14
        ):
            return True
        return False

    @staticmethod
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
            "packet_type": common.PacketType.ACT,
            "sequence_number": None,
            "source_serial_id": bare_packet.u32_at(3),
            "source_logical_id": bare_packet.u8_at(0),
            "lqi": bare_packet.u8_at(11),
            "supply_voltage": None,
            "command_id": bare_packet.u8_at(2),
            "data": bare_packet.payload[14:],
        }
        return ParsedPacket(**parsed_packet_data)
