# -*- coding:utf-8 -*-
# Written for Python 3.12
# Formatted with Black

# Packet parser for App_IO

from datetime import datetime
from typing import Any, final

from overrides import override
from pydantic import Field

from .. import common


@final
class ParsedPacket(common.ParsedPacketBase):
    """Dataclass for parsed packets from App_IO

    Attributes
    ----------
    relay_count: common.UInt8
        Number of relay stations
    di_state: common.CrossSectional[bool]
        Input state for each DI ports
    di_valid: common.CrossSectional[bool]
        Valid state for each DI ports; True if used
    di_interrupt: common.CrossSectional[bool]
        Interrupt state for each DI ports; True if detected via ISR
    """

    relay_count: common.UInt8 = Field(
        default=common.UInt8(0), ge=common.UInt8(0), le=common.UInt8(3)
    )
    di_state: common.CrossSectional[bool] = Field(
        default=common.CrossSectional[bool](12, [False for _ in range(12)])
    )
    di_valid: common.CrossSectional[bool] = Field(
        default=common.CrossSectional[bool](12, [False for _ in range(12)])
    )
    di_interrupt: common.CrossSectional[bool] = Field(
        default=common.CrossSectional[bool](12, [False for _ in range(12)])
    )


@final
class PacketParser(common.PacketParserBase):
    """Packet parser for App_IO"""

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
            and bare_packet.u8_at(3) == 0x02
            and (bare_packet.u8_at(5) & 0x80) == 0x80
            and len(bare_packet.payload) == 20
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
            "packet_type": common.PacketType.APP_IO,
            "sequence_number": bare_packet.u16_at(10),
            "source_serial_id": bare_packet.u32_at(5),
            "source_logical_id": bare_packet.u8_at(0),
            "lqi": bare_packet.u8_at(4),
            "supply_voltage": None,  # There's no ADC
            "relay_count": bare_packet.u8_at(12),
            "di_state": common.CrossSectional[bool](
                12,
                [bool(bare_packet.u16_at(13) & (1 << port)) for port in range(12)],
            ),
            "di_valid": common.CrossSectional[bool](
                12,
                [bool(bare_packet.u16_at(15) & (1 << port)) for port in range(12)],
            ),
            "di_interrupt": common.CrossSectional[bool](
                12,
                [bool(bare_packet.u16_at(17) & (1 << port)) for port in range(12)],
            ),
        }
        return ParsedPacket(**parsed_packet_data)
