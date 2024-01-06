import time
import numpy as np
import heartpy as hp
from math import sqrt, pow
from filters import LiveLFilter, LiveSosFilter, get_heartbeat_filter

start_time = time.time()
# Create a numpy moving average buffer of 100 samples
acc_buffer_length = 2
# acc_x_buffer = np.zeros(acc_buffer_length)
# acc_y_buffer = np.zeros(acc_buffer_length)
# acc_z_buffer = np.zeros(acc_buffer_length)
acc_buffer = np.zeros(acc_buffer_length)
gsr_range = [0.0, 0.5]
live_filter = get_heartbeat_filter(order=4, cutoff=[0.5, 2.5], btype="bandpass", fs=64,
                         output="sos")

# # https://www.samproell.io/posts/yarppg/yarppg-live-digital-filter/
# def get_heartbeat_filter(order=4, cutoff=[0.5, 2.5], btype="bandpass", fs=30,
#                          output="ba"):
#     """Create live filter with lfilter or sosfilter implmementation.
#     """
#     coeffs = scipy.signal.iirfilter(order, Wn=cutoff, fs=fs, btype=btype,
#                                     ftype="butter", output=output)

#     if output == "ba":
#         return LiveLFilter(*coeffs)
#     elif output == "sos":
#         return LiveSosFilter(coeffs)
#     raise NotImplementedError(f"Unknown output {output!r}")

def convert_range(value, in_min, in_max, out_min=0.0, out_max=1.0):
    in_range = in_max - in_min
    out_range = out_max - out_min
    return (((value - in_min) * out_range) / in_range) + out_min


def get_data_value(data):
    return data.get('device'), data.get('run'), data.get('timestamp'), data.get('value')


def get_data_xyz(data):
    return data.get('device'), data.get('run'), data.get('timestamp'), data.get('x'), data.get('y'), data.get('z')


def accelerometer_event(data, osc_client, db_handler=None, is_quiet=False):
    device_uid, run_tag, timestamp, x, y, z = get_data_xyz(data)
    dt = timestamp - start_time
    if not is_quiet:
        print("acc ", device_uid, dt, x, y, z)

    # # Convert values in the range -90.0 - 90.0 to 0.0 - 1.0
    # x = convert_range(x, -90.0, 90.0)
    # y = convert_range(y, -90.0, 90.0)
    # z = convert_range(z, -90.0, 90.0)

    # # Add the new value to the buffers
    # acc_x_buffer[:-1] = acc_x_buffer[1:]
    # acc_x_buffer[-1] = x
    # acc_y_buffer[:-1] = acc_y_buffer[1:]
    # acc_y_buffer[-1] = y
    # acc_z_buffer[:-1] = acc_z_buffer[1:]
    # acc_z_buffer[-1] = z

    # # Calculate the moving average of the buffer
    # average_x = np.mean(acc_x_buffer)
    # average_y = np.mean(acc_y_buffer)
    # average_z = np.mean(acc_z_buffer)

    value = sqrt(pow(x,2) + pow(y,2) + pow(z,2))
    # print("/e4/acc value", value)
    acc_buffer[:-1] = acc_buffer[1:]
    acc_buffer[-1] = value
    # print("/e4/acc buffer", value)

    if acc_buffer[0] != 0:
        diff = abs((value - acc_buffer[0])/32)
        if not is_quiet:
            print("/e4/acc", diff)
        if osc_client:
            osc_client.send_message("/e4/acc", diff)

            # osc_client.send_message("/e4/acc/x", average_x)
            # osc_client.send_message("/e4/acc/y", average_y)
            # osc_client.send_message("/e4/acc/z", average_z)

    if db_handler:
        db_handler.write_to_influx('acc', device_uid, run_tag, timestamp, None, average_x, average_y, average_z)


def bvp_event(data, osc_client, db_handler=None, is_quiet=False ):
    device_uid, run_tag, timestamp, value = get_data_value(data)
    dt = timestamp - start_time
    if not is_quiet:
        print("bvp", device_uid, timestamp, value)

    # Convert values in the range -500.0 - 500.0 to 0.0 - 1.0
    # bvp = convert_range(value, -80.0, 80.0)
    
    # Process the live BVP data using HeartPy
    filtered_value = live_filter(value)
    bvp = filtered_value
    print(f'>>>>> BVP {value} {filtered_value}')

    # wd, m = hp.process([filtered_value], sample_rate=64)
    # # Calculate heart rate
    # bvp = m['bpm']

    if osc_client:
        osc_client.send_message("/e4/bvp", bvp)

    if db_handler:
        db_handler.write_to_influx('bvp', device_uid, run_tag, timestamp, bvp)  # or value?


def temperature_event(data, osc_client, db_handler=None, is_quiet=False):
    device_uid, run_tag, timestamp, value = get_data_value(data)
    dt = timestamp - start_time
    if not is_quiet:
        print("temp", device_uid, timestamp, value)

    # Convert values in the range 25 - 36 to 0.0 - 1.0
    temp = convert_range(value, 25.0, 36.0)

    if osc_client:
        osc_client.send_message("/e4/temp", temp)

    if db_handler:
        db_handler.write_to_influx('temp', device_uid, run_tag, timestamp, temp)


def gsr_event(data, osc_client, db_handler=None, is_quiet=False):
    device_uid, run_tag, timestamp, value = get_data_value(data)
    dt = timestamp - start_time
    # if not is_quiet:
    #     print("gsr", device_uid, timestamp, value)

    if value < gsr_range[0]:
        gsr_range[0] = value
    if value > gsr_range[1]:
        gsr_range[1] = value

    # Convert values to the range of 0.0 - 1.0    
    gsr = convert_range(value, gsr_range[0], gsr_range[1], 0, 50)
    print("EDA", value, gsr)  

    if osc_client:
        osc_client.send_message("/e4/gsr", gsr)

    if db_handler:
        db_handler.write_to_influx('gsr', device_uid, run_tag, timestamp, gsr)


def tag_event(data, osc_client, db_handler=None, is_quiet=False ):
    device_uid, run_tag, timestamp, value = get_data_value(data)
    dt = timestamp - start_time
    if not is_quiet:
        print("tag", device_uid, timestamp, value)

    if osc_client:
        osc_client.send_message("/e4/tag", value)

    if db_handler:
        db_handler.write_to_influx('tag', device_uid, run_tag, timestamp, value)
