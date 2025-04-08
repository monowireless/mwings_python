# -*- coding:utf-8 -*-
# Written for Python 3.12
# Formatted with Black

# Packet serializer for App_PAL (NOTICE) commands

from typing import Any, final

from pydantic import Field, field_serializer
from overrides import override

from .. import common
from .. import utils


@final
class Command(common.CommandBase):
    """Dataclass for App_PAL (NOTICE) command

    Attributes
    ----------
    color : common.AppPalNoticeColor
        Color
    blink_speed : common.AppPalNoticeBlinkSpeed
        Blinking speed
    brightness : common.UInt8
        Brightness from 0 to 0xF
    duration_in_sec : common.UInt8
        Duration in seconds
    """

    color: common.AppPalNoticeColor = Field(default=common.AppPalNoticeColor.WHITE)
    blink_speed: common.AppPalNoticeBlinkSpeed = Field(
        default=common.AppPalNoticeBlinkSpeed.ALWAYS_ON
    )
    brightness: common.UInt8 = Field(
        default=common.UInt8(0x8), ge=common.UInt8(0), le=common.UInt8(0xF)
    )
    duration_in_sec: common.UInt8 = Field(
        default=common.UInt8(5), ge=common.UInt8(0), le=common.UInt8(0xFF)
    )

    @field_serializer("color")
    def serialize_color(self, color: common.AppPalNoticeColor) -> str:
        """Print color in readable names for JSON or something

        Parameters
        ----------
        color : common.AppPalNoticeColor
            Color

        Returns
        -------
        str
            Serialized text for JSON or something
        """

        return color.name

    @field_serializer("blink_speed")
    def serialize_blink_speed(self, blink_speed: common.AppPalNoticeBlinkSpeed) -> str:
        """Print blink_speed in readable names for JSON or something

        Parameters
        ----------
        blink_speed : common.AppPalNoticeBlinkSpeed
            Blinking speed

        Returns
        -------
        str
            Serialized text for JSON or something
        """

        return blink_speed.name

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
        payload_to_build.append(0x02)

        # Set color, speed and brightness
        payload_to_build.append(0x01)
        payload_to_build.append(command.color)
        payload_to_build.append(command.blink_speed)
        payload_to_build.append(command.brightness)

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
