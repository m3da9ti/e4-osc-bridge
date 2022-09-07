import time
import sys

import argparse
from e4client import *
from pythonosc.udp_client import SimpleUDPClient

E4_IP = "127.0.0.1"
E4_PORT = 28000

OSC_IP = "127.0.0.1"
OSC_PORT = 8888

osc_client = None

def accelerometer_event(stream_id, timestamp, *sample):
    print("acc ", stream_id, timestamp, *sample)
    osc_client.send_message("/e4/acc", *sample)

def temperature_event(stream_id, timestamp, *sample):
    print("temp", stream_id, timestamp, *sample)
    osc_client.send_message("/e4/temp", *sample)

def start_streaming_client(e4_ip, e4_port, osc_ip, osc_port):
    global osc_client
    osc_client = SimpleUDPClient(osc_ip, osc_port)

    with E4StreamingClient(E4_IP, E4_PORT) as e4_client:
        devices = e4_client.list_connected_devices()
        print("E4 Devices:", devices)
        if len(devices) == 0:
            print("No E4 devices found.")
            sys.exit(0)

        with e4_client.connect_to_device(devices[0]) as conn:
            conn.subscribe_to_stream(E4DataStreamID.ACC, accelerometer_event)
            conn.subscribe_to_stream(E4DataStreamID.TEMP, temperature_event)

            while True:
                time.sleep(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Forward E4 Streaming Server messages to OSC.')
    parser.add_argument('--e4-ip', type=str, help='E4 streaming server IP address', default='127.0.0.1')
    parser.add_argument('--e4-port', type=int, help='E4 streaming server port', default=28000)
    parser.add_argument('--osc-ip', type=str, help='OSC server IP address', default='127.0.0.1')
    parser.add_argument('--osc-port', type=int, help='OSC server port', default=8888)
    args = parser.parse_args()
    print(args)

    start_streaming_client(args.e4_ip, args.e4_port, args.osc_ip, args.osc_port)
    



