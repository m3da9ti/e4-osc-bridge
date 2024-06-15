import time
import numpy as np
from math import sqrt, pow
from scipy.signal import butter, filtfilt, find_peaks, lfilter, iirfilter
from scipy.ndimage import gaussian_filter1d
from collections import deque
from hr_calc import calculate_hr as bvp_calculate_hr

start_time = time.time()
# Create a numpy moving average buffer of 100 samples
acc_buffer_length = 2
# acc_x_buffer = np.zeros(acc_buffer_length)
# acc_y_buffer = np.zeros(acc_buffer_length)
# acc_z_buffer = np.zeros(acc_buffer_length)
acc_buffer = np.zeros(acc_buffer_length)
gsr_range = [0.0, 0.5]
bvp_queue = deque(maxlen=600)

# Initialize your GSR buffer, OSC client, and other parameters
gsr_buffer_length = 4  # Example length, adjust as needed
gsr_buffer = [0] * gsr_buffer_length
gsr_fs = 4  # Sampling rate (e.g., 4 Hz)

def convert_range(value, in_min, in_max, out_min=0.0, out_max=1.0):
    in_range = in_max - in_min
    out_range = out_max - out_min
    return (((value - in_min) * out_range) / in_range) + out_min


def get_data_value(data):
    return data.get('device'), data.get('run'), data.get('timestamp'), data.get('value')


def get_data_xyz(data):
    return data.get('device'), data.get('run'), data.get('timestamp'), data.get('x'), data.get('y'), data.get('z')


def accelerometer_event(data, osc_clients, db_handler=None, is_quiet=False):
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
        for osc_client in osc_clients:
            osc_client.send_message("/e4/acc", diff)

            #for osc_client in osc_clients:
            # osc_client.send_message("/e4/acc/x", average_x)
            # osc_client.send_message("/e4/acc/y", average_y)
            # osc_client.send_message("/e4/acc/z", average_z)

    # THERE IS AN ISSUE HERE WITH average_x/y/z not being defined
    # if db_handler:
    #     db_handler.write_to_influx('acc', device_uid, run_tag, timestamp, None, average_x, average_y, average_z)


def bvp_event(data, osc_clients, db_handler=None, is_quiet=False):
    device_uid, run_tag, timestamp, value = get_data_value(data)
    dt = timestamp - start_time
    if not is_quiet:  
         print("bvp", device_uid, timestamp, value)

    # Convert values in the range -500.0 - 500.0 to 0.0 - 1.0
    # bvp = convert_range(value, -80.0, 80.0)
    bvp = value
    bvp_queue.append(value)

    try:
        if len(bvp_queue) == bvp_queue.maxlen:
            # buffer is filled
            hr,_,ibi_mean,_ = bvp_calculate_hr(bvp_queue)

            if not is_quiet:  
                # print("hr", device_uid, timestamp, hr)
                print("ibi", device_uid, timestamp, ibi_mean)

            for osc_client in osc_clients:
                # osc_client.send_message("/e4/hr", hr)
                osc_client.send_message("/e4/ibi", ibi_mean)

        for osc_client in osc_clients:
            osc_client.send_message("/e4/bvp", bvp)

    except:
        print('oops shit just happened')

    if db_handler:
        db_handler.write_to_influx('bvp', device_uid, run_tag, timestamp, bvp)  # or value?


def temperature_event(data, osc_clients, db_handler=None, is_quiet=False):
    device_uid, run_tag, timestamp, value = get_data_value(data)
    dt = timestamp - start_time
    if not is_quiet:
        print("temp", device_uid, timestamp, value)

    # Convert values in the range 25 - 36 to 0.0 - 1.0
    temp = convert_range(value, 25.0, 36.0)

    for osc_client in osc_clients:
        osc_client.send_message("/e4/temp", temp)

    if db_handler:
        db_handler.write_to_influx('temp', device_uid, run_tag, timestamp, temp)


def gsr_event(data, osc_clients, db_handler=None, is_quiet=False):
    device_uid, run_tag, timestamp, value = get_data_value(data)
    dt = timestamp - start_time
    if not is_quiet:
        print("gsr", device_uid, timestamp, value)

    # if value < gsr_range[0]:
    #     gsr_range[0] = value
    # if value > gsr_range[1]:
    #     gsr_range[1] = value

    # Convert values to the range of 0.0 - 1.0    
    # gsr = convert_range(value, gsr_range[0], gsr_range[1], 0, 50)
    # print("EDA", value, gsr)  
    # Assuming gsr_buffer, fs (sampling rate), and other necessary setup are already defined

    # for db update
    gsr = value

    # Update the buffer with the new GSR data
    gsr_buffer[:-1] = gsr_buffer[1:]
    gsr_buffer[-1] = value

    # Calculate the rate of change if the first element is not zero (buffer is filled)
    if gsr_buffer[0] != 0:
        gsr_diff = abs((gsr_buffer[-1] - gsr_buffer[0]) / gsr_fs)  # Dividing by the sampling rate

        # Process the difference (e.g., print or send via OSC)
        if not is_quiet:
            print("/e4/gsr", gsr_diff)
        for osc_client in osc_clients:
            osc_client.send_message("/e4/gsr", gsr_diff)

    # for osc_client in osc_clients:
    #     osc_client.send_message("/e4/gsr", gsr)

    if db_handler:
        db_handler.write_to_influx('gsr', device_uid, run_tag, timestamp, gsr)


def tag_event(data, osc_clients, db_handler=None, is_quiet=False):
    device_uid, run_tag, timestamp, value = get_data_value(data)
    dt = timestamp - start_time
    if not is_quiet:
        print("tag", device_uid, timestamp, value)

    for osc_client in osc_clients:
        osc_client.send_message("/e4/tag", value)

    if db_handler:
        db_handler.write_to_influx('tag', device_uid, run_tag, timestamp, value)
