# -*- coding:utf-8 -*-
# Written for Python 3.12
# Formatted with Black

# MWings example: Receive CUE MOT data, calculate angles

# <App_CUE settings>
## Transmission Interval (t): 1+ (e.g. 5)
## Senser Parameter (p): 03000xxx (e.g. 03000000)
## See https://twelite.net/manuals/twelite-stage-sdk/twelite-apps/app-cue/latest/settings/interactive-mode.html

from zoneinfo import ZoneInfo

import statistics
import math

import mwings as mw


# Main function
def main() -> None:
    # Create a twelite object
    twelite = mw.Twelite(mw.utils.ask_user_for_port())

    # Use JST for received data
    twelite.set_timezone(ZoneInfo("Asia/Tokyo"))

    # Register an event handler
    @twelite.on(mw.common.PacketType.APP_PAL_MOT)
    def on_app_cue_pal_mot(packet: mw.parsers.app_pal_mot.ParsedPacket) -> None:
        # Show time parsed
        if packet.time_parsed is not None:
            print(packet.time_parsed.strftime("%Y-%m-%d %H:%M:%S"))

        # Calculate average of 16 samples in the packet
        average_x = statistics.mean(packet.samples_x)
        average_y = statistics.mean(packet.samples_y)
        average_z = statistics.mean(packet.samples_z)
        print(
            f"x(average): {average_x:+04}mg, y(average): {average_y:+04}mg, z(average): {average_z:+04}mg"
        )

        # Calculate angles
        x, y, z = average_x / 1000.0, average_y / 1000.0, average_z / 1000.0
        # Pitch (θ): X-Z plane
        pitch = math.degrees(math.atan2(x, math.sqrt(y**2 + z**2)))
        # Roll (φ): Y-Z plane
        roll = math.degrees(math.atan2(y, math.sqrt(x**2 + z**2)))
        # Yaw (ψ): X-Y plane (reference value)
        yaw = math.degrees(math.atan2(y, x))
        print(
            f"pitch(X-Z): {pitch:+.2f}°, roll(Y-Z): {roll:+.2f}°, yaw(X-Y): {yaw:+.2f}°"
        )

    # Start receiving
    try:
        # Set as daemon thread
        twelite.daemon = True
        # Start the thread, Join to the main thread
        twelite.start()
        print("Started receiving")
        while True:
            twelite.join(0.5)
    except KeyboardInterrupt:
        # Stop the thread
        print("Flushing...")
        twelite.stop()
        print("Completed")


if __name__ == "__main__":
    # Call the main function
    main()
