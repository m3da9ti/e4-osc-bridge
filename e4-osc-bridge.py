from lib2to3.pytree import convert
import time
import sys
from functools import partial
from contextlib import ExitStack

import argparse
import numpy as np
from e4client import *
from pythonosc.udp_client import SimpleUDPClient

# E4_IP = "127.0.0.1"
# E4_PORT = 28000

# OSC_IP = "127.0.0.1"
# OSC_PORT = 8888

VALID_TYPES = ['acc', 'bvp', 'temp', 'gsr', 'tag']

osc_client = None

# Create a numpy moving average buffer of 100 samples
acc_buffer_length = 10
acc_x_buffer = np.zeros(acc_buffer_length)
acc_y_buffer = np.zeros(acc_buffer_length)
acc_z_buffer = np.zeros(acc_buffer_length)

record_log_file = None
print_events = True

start_time = time.time()

def convert_range(value, in_min, in_max, out_min=0.0, out_max=1.0):
    in_range = in_max - in_min
    out_range = out_max - out_min
    return (((value - in_min) * out_range) / in_range) + out_min

def accelerometer_event(device_uid, stream_id, timestamp, *sample):
    dt = timestamp - start_time
    if print_events:
        print("acc ", device_uid, dt, *sample)

    # Convert values in the range -90.0 - 90.0 to 0.0 - 1.0
    x = convert_range(sample[0], -90.0, 90.0)
    y = convert_range(sample[1], -90.0, 90.0)
    z = convert_range(sample[2], -90.0, 90.0)

    # Add the new value to the buffers
    acc_x_buffer[:-1] = acc_x_buffer[1:]
    acc_x_buffer[-1] = x
    acc_y_buffer[:-1] = acc_y_buffer[1:]
    acc_y_buffer[-1] = y
    acc_z_buffer[:-1] = acc_z_buffer[1:]
    acc_z_buffer[-1] = z
    
    # Calculate the moving average of the buffer
    average_x = np.mean(acc_x_buffer)
    average_y = np.mean(acc_y_buffer)
    average_z = np.mean(acc_z_buffer)

    #print("/e4/acc/x", avg)
    osc_client.send_message("/e4/acc/x", average_x)
    osc_client.send_message("/e4/acc/y", average_y)
    osc_client.send_message("/e4/acc/z", average_z)

    if record_log_file is not None:
        record_log_file.write(f"{dt:.02f},{device_uid},acc,{sample[0]:0.2f},{sample[1]:0.2f},{sample[2]:0.2f}\n")

def bvp_event(device_uid, stream_id, timestamp, *sample):
    dt = timestamp - start_time
    if print_events:
        print("bvp", device_uid, timestamp, *sample)

    # Convert values in the range -500.0 - 500.0 to 0.0 - 1.0
    bvp = convert_range(sample[0], -80.0, 80.0)

    osc_client.send_message("/e4/bvp", bvp)

    if record_log_file is not None:
        record_log_file.write(f"{dt:.02f},{device_uid},bvp,{sample[0]:0.2f}\n")


def temperature_event(device_uid, stream_id, timestamp, *sample):
    dt = timestamp - start_time
    if print_events:
        print("temp", device_uid, timestamp, *sample)

    # Convert values in the range 25 - 36 to 0.0 - 1.0
    temp = convert_range(sample[0], 25.0, 36.0)

    osc_client.send_message("/e4/temp", temp)

    if record_log_file is not None:
        record_log_file.write(f"{dt:.02f},{device_uid},temp,{sample[0]:0.2f}\n")


def gsr_event(device_uid, stream_id, timestamp, *sample):
    dt = timestamp - start_time
    if print_events:
        print("gsr", device_uid, timestamp, *sample)

    # Convert values in the range 0.03 - 0.12 to 0.0 - 1.0
    gsr = convert_range(sample[0], 0.06, 0.08)

    osc_client.send_message("/e4/gsr", gsr)

    if record_log_file is not None:
        record_log_file.write(f"{dt:.02f},{device_uid},gsr,{sample[0]:0.6f}\n")

def tag_event(device_uid, stream_id, timestamp, *sample):
    dt = timestamp - start_time
    if print_events:
        print("tag", device_uid, timestamp, *sample)

    osc_client.send_message("/e4/tag", sample[0])

    if record_log_file is not None:
        record_log_file.write(f"{dt:.02f},{device_uid},tag,{sample[0]}\n")

def start_streaming_client(e4_ip, e4_port, osc_ip, osc_port, event_types):
    global osc_client
    osc_client = SimpleUDPClient(osc_ip, osc_port)

    with E4StreamingClient(e4_ip, e4_port) as e4_client:
        devices = list(e4_client.list_connected_devices())
        print("E4 Devices:", devices)
        if len(devices) == 0:
            print("No E4 devices found.")
            sys.exit(0)

    # We need to setup multiple TCP connections, one for each device.

    with ExitStack() as stack:
        for device in devices:
            e4_client = E4StreamingClient(e4_ip, e4_port)
            stack.enter_context(e4_client)
            print(device)
            conn = e4_client.connect_to_device(device)
            stack.enter_context(conn)
            uid = device.uid
            if 'acc' in event_types:
                conn.subscribe_to_stream(E4DataStreamID.ACC, partial(accelerometer_event, uid))
            
            if 'bvp' in event_types:
                conn.subscribe_to_stream(E4DataStreamID.BVP, partial(bvp_event, uid))

            if 'temp' in event_types:
                conn.subscribe_to_stream(E4DataStreamID.TEMP, partial(temperature_event, uid))
            
            if 'gsr' in event_types:
                conn.subscribe_to_stream(E4DataStreamID.GSR, partial(gsr_event, uid))

            if 'tag' in event_types:
                conn.subscribe_to_stream(E4DataStreamID.TAG, partial(tag_event, uid))


        while True:
            time.sleep(1)

def start_replay(replay_log_file, osc_ip, osc_port, event_types):
    global osc_client
    osc_client = SimpleUDPClient(osc_ip, osc_port)

    log_file = open(replay_log_file, "r")
    last_time = 0
    # Order the timestamps in the log file
    events = []
    for line in log_file:
        line = line.strip()
        event_time, device_uid, event_type, *sample = line.split(",")
        event_time = float(event_time)
        sample = [float(x) for x in sample]
        events.append((event_time, device_uid, event_type, sample))
    events.sort(key=lambda x: x[0])

    # Now replay the sorted events
    while True:
        for event_time, device_uid, event_type, sample in events:
            # Sleep until the event time
            time.sleep(abs(event_time - last_time))
            last_time = event_time

            if event_type not in event_types:
                continue

            if event_type == "acc":
                accelerometer_event(device_uid, 0, event_time, *sample)
            elif event_type == "temp":
                temperature_event(device_uid, 0, event_time, *sample)
            elif event_type == "bvp":
                bvp_event(device_uid, 0, event_time, *sample)
            elif event_type == "gsr":
                gsr_event(device_uid, 0, event_time, *sample)
            elif event_type == "tag":
                tag_event(device_uid, 0, event_time, *sample)

        # Loop the replay
        print("Replay finished, looping...")
        last_time = 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Forward E4 Streaming Server messages to OSC.')
    parser.add_argument('--e4-ip', type=str, help='E4 streaming server IP address', default='127.0.0.1')
    parser.add_argument('--e4-port', type=int, help='E4 streaming server port', default=28000)
    parser.add_argument('--osc-ip', type=str, help='OSC server IP address', default='127.0.0.1')
    parser.add_argument('--osc-port', type=int, help='OSC server port', default=8000)
    parser.add_argument('--record', type=str, help='Log E4 streams to file', default=None)
    parser.add_argument('--replay', type=str, help='Replays an existing log file', default=None)
    parser.add_argument('--type', type=str, help='Filters the event type, separated by commas (e.g. bvp, gsr)', default=None)
    parser.add_argument('--quiet', action='store_true', help='Don\'t log out all events')

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

    if args.quiet:
        print_events = False

    if args.replay and args.record:
        print("Cannot record and replay at the same time.")
        sys.exit(0)
    if args.replay:
        start_replay(args.replay, args.osc_ip, args.osc_port, types)
    else:
        if args.record is not None:
            record_log_file = open(args.record, "w")

        start_streaming_client(args.e4_ip, args.e4_port, args.osc_ip, args.osc_port, types)
