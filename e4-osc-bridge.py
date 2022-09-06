import time
import sys

from e4client import *
from pythonosc.udp_client import SimpleUDPClient

E4_IP = "127.0.0.1"
E4_PORT = 28000

OSC_IP = "127.0.0.1"
OSC_PORT = 8888

osc_client = SimpleUDPClient(OSC_IP, OSC_PORT)

def accelerometer_event(stream_id, timestamp, *sample):
    print("acc ", stream_id, timestamp, *sample)
    osc_client.send_message("/e4/acc", *sample)

def temperature_event(stream_id, timestamp, *sample):
    print("temp", stream_id, timestamp, *sample)
    osc_client.send_message("/e4/temp", *sample)

if __name__ == "__main__":
    with E4StreamingClient(E4_IP, E4_PORT) as e4_client:
        devices = e4_client.list_connected_devices()
        print("Devices:", devices)
        if len(devices) == 0:
            print("No devices found.")
            sys.exit(0)

        with e4_client.connect_to_device(devices[0]) as conn:
            conn.subscribe_to_stream(E4DataStreamID.ACC, accelerometer_event)
            conn.subscribe_to_stream(E4DataStreamID.TEMP, temperature_event)

            while True:
                time.sleep(1)
