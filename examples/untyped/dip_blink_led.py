# -*- coding:utf-8 -*-
# TWELITE DIP start guide: blinking from python

from time import sleep

import mwings as mw


def main():
    twelite = mw.Twelite(mw.utils.ask_user_for_port())

    initial = {
        "destination_logical_id": 0x78,
        "di_to_change": [True, False, False, False],
        "di_state": [False, False, False, False],
    }
    command = mw.serializers.app_twelite.Command(**initial)

    while True:
        command.di_state[0] = not command.di_state[0]
        twelite.send(command)
        print(f"Flip DO1: {command.di_state[0]}")
        sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("...Aborting")
