# -*- coding:utf-8 -*-
# Written for Python 3.12
# Formatted with Black

# Packet serializer for App_UART (Mode A) commands

from typing import final

from pydantic import Field
from overrides import override

from .. import common


@final
class Command(common.CommandBase):
    """Dataclass for App_UART (Mode A) command

    Attributes
    ----------
    command_id : common.UInt8
        Command id
    data : bytes
        Data to send
    """

    command_id: common.UInt8 = Field(
        default=common.UInt8(0), ge=common.UInt8(0), lt=common.UInt8(0x80)
    )
    data: bytes = Field(min_length=1, max_length=80)

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

        return (
            0x00 <= self.destination_logical_id <= 0x64
            or self.destination_logical_id == 0x78
        )


@final
class CommandSerializer(common.CommandSerializerBase):
    """Command serializer for App_Uart (Mode A)"""

    @staticmethod
    @override
    def serialize(command: common.SomeCommand) -> common.BarePacket | None:
        """Serialize the given command

        Parameters
        ----------
        command : common.SomeCommand
            App_Uart (Mode A) command to serialize

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

        return common.BarePacket(
            payload=command.data,
            logical_and_command_id=(command.destination_logical_id, command.command_id),
        )
