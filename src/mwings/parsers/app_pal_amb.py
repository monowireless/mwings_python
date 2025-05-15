# -*- coding:utf-8 -*-
# Written for Python 3.12
# Formatted with Black

# Packet parser for App_PAL (AMB)

from datetime import datetime
from typing import Any, final

from overrides import override
from pydantic import Field

from .. import common


@final
class ParsedPacket(common.ParsedPacketBase):
    """Dataclass for parsed packets from App_PAL (AMB)

    Attributes
    ----------
    router_serial_id: UInt32
        Serial ID for the first router device (0x80000000 with no routing)
    ai1_voltage: common.UInt16
        Voltage for AI1 port in mV
    temp_100x: common.Int16
        100x temperature in °C
    humid_100x: common.UInt16
        100x humidity in RH%
    illuminance: common.UInt32
        Illuminance in lux
    """

    router_serial_id: common.UInt32 = Field(
        default=common.UInt32(0), ge=common.UInt32(0), le=common.UInt32(0xFFFFFFFF)
    )
    ai1_voltage: common.UInt16 = Field(
        default=common.UInt16(0), ge=common.UInt16(0), le=common.UInt16(3700)
    )
    temp_100x: common.Int16 = Field(
        default=common.Int16(0), ge=common.Int16(-4000), le=common.Int16(12500)
    )
    humid_100x: common.UInt16 = Field(
        default=common.UInt16(0), ge=common.UInt16(0), le=common.UInt16(10000)
    )
    illuminance: common.UInt32 = Field(
        default=common.UInt32(0), ge=common.UInt32(0), le=common.UInt32(157000)
    )


@final
class PacketParser(common.PacketParserBase):
    """Packet parser for App_PAL (AMB)"""

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
            (bare_packet.u8_at(0) & 0x80) == 0x80
            and (bare_packet.u8_at(7) & 0x80) == 0x80
            and bare_packet.u8_at(12) == 0x80
            and bare_packet.u8_at(13) == 0x82
            and len(bare_packet.payload) == 48
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
            "packet_type": common.PacketType.APP_PAL_AMB,
            "sequence_number": bare_packet.u16_at(5),
            "source_serial_id": bare_packet.u32_at(7),
            "source_logical_id": bare_packet.u8_at(11),
            "lqi": bare_packet.u8_at(4),
            "supply_voltage": bare_packet.u16_at(19),
            "router_serial_id": bare_packet.u32_at(0),
            "ai1_voltage": bare_packet.u16_at(25),
            "temp_100x": bare_packet.i16_at(31),
            "humid_100x": bare_packet.u16_at(37),
            "illuminance": bare_packet.u32_at(43),
        }
        return ParsedPacket(**parsed_packet_data)
