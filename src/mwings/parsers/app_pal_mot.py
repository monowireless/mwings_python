# -*- coding:utf-8 -*-
# Written for Python 3.12
# Formatted with Black

# Packet parser for App_PAL (MOT, accel)

from datetime import datetime
from typing import Any, final

from overrides import override
from pydantic import Field, field_validator

from .. import common


@final
class ParsedPacket(common.ParsedPacketBase):
    """Dataclass for parsed packets from App_PAL (MOT)

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
    sampling_frequency: UInt16
        Sampling frequency in Hz
    """

    router_serial_id: common.UInt32 = Field(
        default=common.UInt32(0), ge=common.UInt32(0), le=common.UInt32(0xFFFFFFFF)
    )
    ai1_voltage: common.UInt16 = Field(
        default=common.UInt16(0), ge=common.UInt16(0), le=common.UInt16(3700)
    )
    sample_count: common.UInt8 = Field(
        default=common.UInt8(16), ge=common.UInt8(16), le=common.UInt8(16)
    )
    samples_x: common.TimeSeries[common.Int16] = Field(
        default=common.TimeSeries[common.Int16](
            16, [common.Int16(0) for _ in range(16)]
        )
    )
    samples_y: common.TimeSeries[common.Int16] = Field(
        default=common.TimeSeries[common.Int16](
            16, [common.Int16(0) for _ in range(16)]
        )
    )
    samples_z: common.TimeSeries[common.Int16] = Field(
        default=common.TimeSeries[common.Int16](
            16, [common.Int16(0) for _ in range(16)]
        )
    )
    sampling_frequency: common.UInt16 = Field(default=common.UInt16(25))

    @field_validator("sampling_frequency")
    @classmethod
    def check_sampling_frequency(cls, freq: int) -> int:
        """Check for sampling_frequency

        Parameters
        ----------
        freq : int
            Input

        Returns
        -------
        int
            Valid input

        Raises
        ------
        ValueError
            Raise if the specified frequency is not supported
        """

        if freq not in set(
            [
                25,
                50,
                100,
                190,
                380,
                750,
                1100,
                1300,
            ]
        ):
            raise ValueError("not supported")
        return freq


@final
class PacketParser(common.PacketParserBase):
    """Packet parser for App_PAL (MOT)"""

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
            and bare_packet.u8_at(13) == 0x83
            and len(bare_packet.payload) == 188
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
        frequencies = common.FixedTuple[common.UInt16](
            8,
            [
                common.UInt16(25),
                common.UInt16(50),
                common.UInt16(100),
                common.UInt16(190),
                common.UInt16(380),
                common.UInt16(750),
                common.UInt16(1100),
                common.UInt16(1300),
            ],
        )
        parsed_packet_data: dict[str, Any] = {
            "time_parsed": datetime.now(common.Timezone),
            "packet_type": common.PacketType.APP_PAL_MOT,
            "sequence_number": bare_packet.u16_at(5),
            "source_serial_id": bare_packet.u32_at(7),
            "source_logical_id": bare_packet.u8_at(11),
            "lqi": bare_packet.u8_at(4),
            "supply_voltage": bare_packet.u16_at(19),
            "router_serial_id": bare_packet.u32_at(0),
            "ai1_voltage": bare_packet.u16_at(25),
            "sample_count": 16,
            "samples_x": common.TimeSeries[common.Int16](
                16,
                [bare_packet.i16_at(31 + (10 * index) + 0) for index in range(16)],
            ),
            "samples_y": common.TimeSeries[common.Int16](
                16,
                [bare_packet.i16_at(31 + (10 * index) + 2) for index in range(16)],
            ),
            "samples_z": common.TimeSeries[common.Int16](
                16,
                [bare_packet.i16_at(31 + (10 * index) + 4) for index in range(16)],
            ),
            "sampling_frequency": frequencies[bare_packet.u8_at(29) >> 5],
        }
        return ParsedPacket(**parsed_packet_data)
