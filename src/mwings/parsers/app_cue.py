# -*- coding:utf-8 -*-
# Written for Python 3.12
# Formatted with Black

# Packet parser for App_CUE (CUE mode)

from datetime import datetime
from typing import Any, final

from overrides import override
from pydantic import Field, field_serializer

from .. import common


@final
class ParsedPacket(common.ParsedPacketBase):
    """Dataclass for parsed packets from App_CUE

    Attributes
    ----------
    router_serial_id: UInt32
        Serial ID for the first router device (0x80000000 with no routing)
    ai1_voltage: common.UInt16
        Voltage for AI1 port in mV
    sample_count: common.UInt8
        Number of accel samples
    samples_x: common.TimeSeries[common.Int16]
        Accel samples for x axis
    samples_y: common.TimeSeries[common.Int16]
        Accel samples for y axis
    samples_z: common.TimeSeries[common.Int16]
        Accel samples for z axis
    has_accel_event: bool
        True if an accel event is available
    accel_event: common.AccelEvent
        Accel event
    magnet_state: common.MagnetState
        Magnet state
    magnet_state_changed: bool
        True if the magnet state was changed
    """

    router_serial_id: common.UInt32 = Field(
        default=common.UInt32(0), ge=common.UInt32(0), le=common.UInt32(0xFFFFFFFF)
    )
    ai1_voltage: common.UInt16 = Field(
        default=common.UInt16(0), ge=common.UInt16(0), le=common.UInt16(3600)
    )
    sample_count: common.UInt8 = Field(
        default=common.UInt8(10), ge=common.UInt8(10), le=common.UInt8(10)
    )
    samples_x: common.TimeSeries[common.Int16] = Field(
        default=common.TimeSeries[common.Int16](
            10, [common.Int16(0) for _ in range(10)]
        )
    )
    samples_y: common.TimeSeries[common.Int16] = Field(
        default=common.TimeSeries[common.Int16](
            10, [common.Int16(0) for _ in range(10)]
        )
    )
    samples_z: common.TimeSeries[common.Int16] = Field(
        default=common.TimeSeries[common.Int16](
            10, [common.Int16(0) for _ in range(10)]
        )
    )
    has_accel_event: bool = Field(default=False)
    accel_event: common.AccelEvent = Field(default=common.AccelEvent.NONE)
    magnet_state: common.MagnetState = Field(default=common.MagnetState.NOT_DETECTED)
    magnet_state_changed: bool = Field(default=False)

    @field_serializer("accel_event")
    def serialize_accel_event(self, accel_event: common.AccelEvent) -> str:
        """Print accel_event in readable names for JSON or something

        Parameters
        ----------
        accel_event : common.AccelEvent
            Accel event

        Returns
        -------
        str
            Serialized text for JSON or something
        """

        return accel_event.name

    @field_serializer("magnet_state")
    def serialize_magnet_state(self, magnet_state: common.MagnetState) -> str:
        """Print magnet_state in readable names for JSON or something

        Parameters
        ----------
        magnet_state : common.MagnetState
            Magnet state

        Returns
        -------
        str
            Serialized text for JSON or something
        """

        return magnet_state.name


@final
class PacketParser(common.PacketParserBase):
    """Packet parser for App_CUE"""

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
            and bare_packet.u8_at(13) == 0x05
            and len(bare_packet.payload) == 148
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
            "packet_type": common.PacketType.APP_CUE,
            "sequence_number": bare_packet.u16_at(5),
            "source_serial_id": bare_packet.u32_at(7),
            "source_logical_id": bare_packet.u8_at(11),
            "lqi": bare_packet.u8_at(4),
            "supply_voltage": bare_packet.u16_at(34),
            "router_serial_id": bare_packet.u32_at(0),
            "ai1_voltage": bare_packet.u16_at(40),
            "sample_count": 10,
            "samples_x": common.TimeSeries[common.Int16](
                10,
                [bare_packet.i16_at(51 + (10 * index) + 0) for index in range(10)],
            ),
            "samples_y": common.TimeSeries[common.Int16](
                10,
                [bare_packet.i16_at(51 + (10 * index) + 2) for index in range(10)],
            ),
            "samples_z": common.TimeSeries[common.Int16](
                10,
                [bare_packet.i16_at(51 + (10 * index) + 4) for index in range(10)],
            ),
            "has_accel_event": bool(bare_packet.u8_at(24) == 0x04),
            "accel_event": common.AccelEvent(
                bare_packet.u8_at(26) if bare_packet.u8_at(24) == 0x04 else 0xFF
            ),
            "magnet_state": common.MagnetState(bare_packet.u8_at(46) & 0x0F),
            "magnet_state_changed": False if bare_packet.u8_at(46) & 0x80 else True,
        }
        return ParsedPacket(**parsed_packet_data)
