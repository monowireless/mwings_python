# -*- coding:utf-8 -*-
# Written for Python 3.12
# Formatted with Black

# Packet parser for App_Twelite

from datetime import datetime
from typing import Any, final

from overrides import override
from pydantic import Field, field_validator

from .. import common


@final
class ParsedPacket(common.ParsedPacketBase):
    """Dataclass for parsed packets from App_Twelite

    Attributes
    ----------
    destination_logical_id: common.UInt8
        Logical ID for the destination (parent) device
    relay_count: common.UInt8
        Number of relay stations
    periodic: bool
        True if the packet is a periodic transmit packet
    di_changed: common.CrossSectional[bool]
        State for each digital interfaces; True if changed
    di_state: common.CrossSectional[bool]
        Input status for each digital interfaces
    ai_voltage: common.CrossSectional[common.UInt16]
        Voltage in mV for each analog interfaces
    """

    destination_logical_id: common.UInt8 = Field(default=common.UInt8(0x78))
    relay_count: common.UInt8 = Field(
        default=common.UInt8(0), ge=common.UInt8(0), le=common.UInt8(3)
    )
    periodic: bool = Field(default=False)
    di_changed: common.CrossSectional[bool] = Field(
        default=common.CrossSectional[bool](4, [False for _ in range(4)])
    )
    di_state: common.CrossSectional[bool] = Field(
        default=common.CrossSectional[bool](4, [False for _ in range(4)])
    )
    ai_voltage: common.CrossSectional[common.UInt16] = Field(
        default=common.CrossSectional[common.UInt16](
            4, [common.UInt16(0) for _ in range(4)]
        )
    )

    @field_validator("destination_logical_id")
    @classmethod
    def check_destination_logical_id(cls, lid: int) -> int:
        """Check destination lid

        Must be in range between 0 and 100 or 120 and 127 but 122
        (Router) is invalid

        Parameters
        ----------
        lid : int
            Input

        Returns
        -------
        int
            Valid input

        Raises
        ------
        ValueError
            Out of range
        """

        if 0 <= lid <= 100:
            return lid
        elif lid in range(120, 128) and lid != 122:
            return lid
        else:
            raise ValueError("must be in range (0-100) or (120-121/123-127)")

    @field_validator("ai_voltage")
    @classmethod
    def check_ai_voltage(
        cls, aiv: common.CrossSectional[int]
    ) -> common.CrossSectional[int]:
        """Check voltage of analog interfaces

        Must be in range between 0 and 3700 (VCCmax3600+margin100)

        Parameters
        ----------
        aiv : common.CrossSectional
            Input

        Returns
        -------
        common.CrossSectional
            Valid input

        Raises
        ------
        ValueError
            Out of range
        """

        for voltage in aiv:
            if voltage < 0 or voltage > 3700:
                raise ValueError("Out of range")
        return aiv


@final
class PacketParser(common.PacketParserBase):
    """Packet parser for App_Twelite"""

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
            bare_packet.u8_at(1) == 0x81
            and bare_packet.u8_at(3) == 0x01
            and (bare_packet.u8_at(5) & 0x80) == 0x80
            and len(bare_packet.payload) == 23
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
            "packet_type": common.PacketType.APP_TWELITE,
            "sequence_number": bare_packet.u16_at(10),  # In this, timestamp
            "source_serial_id": bare_packet.u32_at(5),
            "source_logical_id": bare_packet.u8_at(0),
            "lqi": bare_packet.u8_at(4),
            "supply_voltage": bare_packet.u16_at(13),
            "destination_logical_id": bare_packet.u8_at(9),
            "relay_count": bare_packet.u8_at(12),
            "periodic": ((bare_packet.u8_at(16) & 0x80) == 0x80),
            "di_state": common.CrossSectional[bool](
                4,
                [bool(bare_packet.u8_at(16) & (1 << port)) for port in range(4)],
            ),
            "di_changed": common.CrossSectional[bool](
                4,
                [bool(bare_packet.u8_at(17) & (1 << port)) for port in range(4)],
            ),
            "ai_voltage": common.CrossSectional[common.UInt16](
                4,
                [
                    common.UInt16(
                        min(
                            bare_packet.u8_at(18 + port) * 16
                            + ((bare_packet.u8_at(22) >> (port * 2)) & 0x03) * 4,
                            2000,
                        )
                    )
                    for port in range(4)
                ],
            ),
        }
        return ParsedPacket(**parsed_packet_data)
