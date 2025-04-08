# -*- coding:utf-8 -*-
# Written for Python 3.12
# Formatted with Black

# Packet serializer for App_PAL (NOTICE) event commands

from typing import Any, final

from pydantic import Field
from overrides import override

from .. import common
from .. import utils


@final
class Command(common.CommandBase):
    """Dataclass for App_PAL (NOTICE) event command

    Attributes
    ----------
    event_id : common.UInt8
        Event id
    """

    event_id: common.UInt8 = Field(
        default=common.UInt8(0), ge=common.UInt8(0), le=common.UInt8(0x10)
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
        payload_to_build.append(0x01)

        # Set event id
        payload_to_build.append(0x00)
        payload_to_build.append(0x04)
        payload_to_build.append(0x00)
        payload_to_build.append(command.event_id)

        serialized_packet: dict[str, Any] = {
            "payload": bytes(payload_to_build),
            "checksum": utils.lrc8(bytes(payload_to_build)),
        }

        return common.BarePacket(**serialized_packet)
