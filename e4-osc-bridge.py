import time
import sys

import argparse
import numpy as np
from e4client import *
from pythonosc.udp_client import SimpleUDPClient

E4_IP = "127.0.0.1"
E4_PORT = 28000

OSC_IP = "127.0.0.1"
OSC_PORT = 8888

osc_client = None

# Create a numpy moving average buffer of 100 samples
acc_buffer_length = 10
acc_x_buffer = np.zeros(acc_buffer_length)
acc_y_buffer = np.zeros(acc_buffer_length)
acc_z_buffer = np.zeros(acc_buffer_length)

event_log_file = None

start_time = time.time()

def accelerometer_event(stream_id, timestamp, *sample):
    dt = timestamp - start_time
    print("acc ", stream_id, dt, *sample)

    # Convert values in the range -90.0 - 90.0 to 0.0 - 1.0
    x = (sample[0] + 90.0) / 180.0
    y = (sample[1] + 90.0) / 180.0
    z = (sample[2] + 90.0) / 180.0

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

    if event_log_file is not None:
        event_log_file.write(f"{dt:.02f},acc,{sample[0]:0.2f},{sample[1]:0.2f},{sample[2]:0.2f}\n")

def temperature_event(stream_id, timestamp, *sample):
    print("temp", stream_id, timestamp, *sample)
    osc_client.send_message("/e4/temp", sample)

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
            #conn.subscribe_to_stream(E4DataStreamID.TEMP, temperature_event)

            while True:
                time.sleep(1)

def start_replay(replay_file, osc_ip, osc_port):
    global osc_client
    osc_client = SimpleUDPClient(osc_ip, osc_port)

    log_file = open(args.log_file, "r")
    last_time = 0
    for line in log_file:
        line = line.strip()
        event_time, event_type, *sample = line.split(",")
        event_time = float(event_time)
        sample = [float(x) for x in sample]

        time.sleep(event_time - last_time)
        last_time = event_time

        if event_type == "acc":
            accelerometer_event(0, event_time, *sample)
        elif event_type == "temp":
            temperature_event(0, event_time, *sample)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Forward E4 Streaming Server messages to OSC.')
    parser.add_argument('--e4-ip', type=str, help='E4 streaming server IP address', default='127.0.0.1')
    parser.add_argument('--e4-port', type=int, help='E4 streaming server port', default=28000)
    parser.add_argument('--osc-ip', type=str, help='OSC server IP address', default='127.0.0.1')
    parser.add_argument('--osc-port', type=int, help='OSC server port', default=8888)
    parser.add_argument('--log-file', type=str, help='Log E4 streams to file', default=None)
    parser.add_argument('--replay', action='store_true', help='Replays an existing log file', default=False)
    args = parser.parse_args()
    print(args)

    if args.replay:
        start_replay(args.log_file, args.osc_ip, args.osc_port)
    else:
        if args.log_file is not None:
            event_log_file = open(args.log_file, "w")

        start_streaming_client(args.e4_ip, args.e4_port, args.osc_ip, args.osc_port)
    



