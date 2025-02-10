# -*- coding:utf-8 -*-
# TWELTIE DIP start guide: receiving in python

import mwings as mw


def main():
    twelite = mw.Twelite(mw.utils.ask_user_for_port())

    @twelite.on(mw.common.PacketType.APP_TWELITE)
    def on_app_twelite(packet):
        if packet.di_state[0]:
            print("DI1 Pressed")

    try:
        twelite.daemon = True
        twelite.start()
        print("Started receiving")
        while True:
            twelite.join(0.5)
    except KeyboardInterrupt:
        print("Flushing...")
        twelite.stop()
        print("Completed")


if __name__ == "__main__":
    main()
