# -*- coding:utf-8 -*-
# Written for Python 3.12
# Formatted with Black

# Packet serializer for App_PAL (NOTICE) detailed commands

from typing import Any, final

from pydantic import Field
from overrides import override

from .. import common
from .. import utils


@final
class Command(common.CommandBase):
    """Dataclass for App_PAL (NOTICE) detailed command

    Attributes
    ----------
    color : common.AppPalNoticeRGBWColor
        Color in RGBW (0-0xF)
    blink_duty_percentage : common.UInt8
        Blink duty in %
    blink_period_in_sec : common.Float64
        Blink period in sec (0-10.2)
    duration_in_sec : common.UInt8
        Duration in seconds
    """

    color: common.AppPalNoticeRGBWColor = Field(default=common.AppPalNoticeRGBWColor())
    blink_duty_percentage: common.UInt8 = Field(
        default=common.UInt8(100), ge=common.UInt8(0), le=common.UInt8(100)
    )
    blink_period_in_sec: common.Float64 = Field(
        default=common.Float64(1.0), ge=common.Float64(0.0), le=common.Float64(10.2)
    )
    duration_in_sec: common.UInt8 = Field(
        default=common.UInt8(1), le=common.UInt8(0xFF)
    )

    @override
    def is_valid(self) -> bool:
        """Check if the command content is valid or not

        Returns
        -------
        bool
            True if valid

        Notes
        -----
        Overridden
        """

        return 0x00 <= self.destination_logical_id <= 0x64


@final
class CommandSerializer(common.CommandSerializerBase):
    """Command serializer for App_PAL (NOTICE)"""

    @staticmethod
    @override
    def serialize(command: common.SomeCommand) -> common.BarePacket | None:
        """Serialize the given command

        Parameters
        ----------
        command : common.SomeCommand
            App_PAL (NOTICE) command to serialize

        Returns
        -------
        common.BarePacket | None
            Serialized bytes and its LRC checksum (8bit) if valid

        Notes
        -----
        Static overridden method
        """

        if not (isinstance(command, Command) and command.is_valid()):
            return None

        payload_to_build: bytearray = bytearray()

        payload_to_build.append(min(command.destination_logical_id, 0x64))
        payload_to_build.append(0x90)
        payload_to_build.append(0x03)

        # Set color in RGBW
        payload_to_build.append(0x03)
        payload_to_build.append(0xFF)
        payload_to_build.append((command.color.u16() >> 8) & 0xFF)
        payload_to_build.append((command.color.u16() >> 0) & 0xFF)

        # Set blinking behavior
        payload_to_build.append(0x04)
        payload_to_build.append(0xFF)
        payload_to_build.append(round(command.blink_duty_percentage * 0xFF / 100))
        payload_to_build.append(round(command.blink_period_in_sec / 0.04))

        # Set duration
        payload_to_build.append(0x02)
        payload_to_build.append(0xFF)
        payload_to_build.append((command.duration_in_sec >> 8) & 0xFF)
        payload_to_build.append((command.duration_in_sec >> 0) & 0xFF)

        serialized_packet: dict[str, Any] = {
            "payload": bytes(payload_to_build),
            "checksum": utils.lrc8(bytes(payload_to_build)),
        }

        return common.BarePacket(**serialized_packet)
