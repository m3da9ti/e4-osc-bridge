import time
import argparse
import sys
from datetime import datetime as dt

import influxdb_client
import numpy as np
from influxdb_client.client.write_api import WritePrecision
from pythonosc.udp_client import SimpleUDPClient

import events
from influx import Influx


VALID_TYPES = ['acc', 'bvp', 'temp', 'gsr', 'tag']

# Create a numpy moving average buffer of 100 samples
acc_buffer_length = 10
acc_x_buffer = np.zeros(acc_buffer_length)
acc_y_buffer = np.zeros(acc_buffer_length)
acc_z_buffer = np.zeros(acc_buffer_length)

start_time = time.time()


def start_replay(device_id, run_tag, osc_ip, osc_port, event_types):
    global osc_client
    osc_client = SimpleUDPClient(osc_ip, osc_port)

    last_time = 0
    # # Order the timestamps in the log file
    # events = []
    # for line in log_file:
    #     line = line.strip()
    #     event_time, device_uid, event_type, *sample = line.split(",")
    #     event_time = float(event_time)
    #     sample = [float(x) for x in sample]
    #     events.append((event_time, device_uid, event_type, sample))
    # events.sort(key=lambda x: x[0])

    # Now replay the sorted events
    while True:
        influx.read_from_influx(device_id, run_tag)

        # for event_time, device_uid, event_type, sample in events:
        #     # Sleep until the event time
        #     time.sleep(abs(event_time - last_time))
        #     last_time = event_time

        #     if event_type not in event_types:
        #         continue

        #     if event_type == "acc":
        #         accelerometer_event(device_uid, 0, event_time, *sample)
        #     elif event_type == "temp":
        #         temperature_event(device_uid, 0, event_time, *sample)
        #     elif event_type == "bvp":
        #         bvp_event(device_uid, 0, event_time, *sample)
        #     elif event_type == "gsr":
        #         gsr_event(device_uid, 0, event_time, *sample)
        #     elif event_type == "tag":
        #         tag_event(device_uid, 0, event_time, *sample)

        # Loop the replay
        # print("Replay finished, looping...")
        last_time = 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Forward stored events to OSC.')
    parser.add_argument('--osc-ip', type=str, help='OSC server IP address', default='127.0.0.1')
    parser.add_argument('--osc-port', type=int, help='OSC server port', default=8000)
    parser.add_argument('--run-tag', type=str, help='Run tag to replay e.g. series-031920231413', default=None)
    parser.add_argument('--device-id', type=str, help='Device ID e.g. ', default='A03FB4')
    parser.add_argument('--type', type=str, help='Filters the event type, separated by commas (e.g. bvp, gsr)',
                        default=None)
    parser.add_argument('--influx-url', type=str, help='Influx URL', default='http://localhost:8086/')
    parser.add_argument('--influx-token', type=str, help='Influx token', default='bKZ6u51oPb3rvWCskPuDWGxR39qiTVosCdUcKmsRxYWhRwYjgVNQajL7668HgAEMDlfCr9dwrxEF2QEpmV0KQQ==')
    parser.add_argument('--influx-bucket', type=str, help='Influx bucket', default='e4-bucket')
    parser.add_argument('--influx-org', type=str, help='Influx Org ID', default='230dc0ec1d83e595')


    args = parser.parse_args()
    types = VALID_TYPES
    if args.type:
        types = args.type.split(',')
        types = [t.strip() for t in types]
        # Check if all types are valid
        for t in types:
            if t not in VALID_TYPES:
                print(f"Invalid event type: {t}")
                sys.exit(0)

    print(f'Connecting to InfluxDB: {args.influx_url}|{args.influx_org}|{args.influx_bucket}')
    influx = Influx(args.influx_url, args.influx_token, args.influx_org, args.influx_bucket)

    start_replay(args.device_id, args.run_tag, args.osc_ip, args.osc_port, types)
