import numpy as np
from scipy.signal import butter, filtfilt, find_peaks, lfilter, iirfilter
from scipy.ndimage import gaussian_filter1d
from collections import deque

def calculate_hr(queue):
    data_array_not_smoothed = [*queue]

    # print(f'RAW: {data_array_not_smoothed}')

    data_array = gaussian_filter1d(data_array_not_smoothed, sigma=2)  # equivalent to MATLAB's smoothdata function

    # print(f'SMOOTH: {data_array}')

    fs = 64  # Sampling rate

    # to make it sharper: ???? 
    # 4 -> 10 more computationally expensive
    # window 2.5 -> 1? 2.5 -> 4? 
    # butter is ok for this case
    b, a = iirfilter(4, Wn=2.5, fs=fs, btype="low", ftype="butter")
    data_array_filt = lfilter(b, a, data_array)

    # print(f'FILTER: {data_array_filt}')

    # Find peaks in the filtered timeseries
    # height might be too high
    peaks, _ = find_peaks(gaussian_filter1d(data_array_filt, sigma=2), height=0.5)

    # print(f'PEAKS: {peaks}')

    # Compute Heart Rate and other metrics from the peaks
    # ... Similar logic to MATLAB for calculating HR, IBI, etc.
    # Calculate the time of each peak (i.e., pulse time)
    tbasis = np.arange(len(data_array_filt)) / fs
    pulse_times = tbasis[peaks]

    # print(f'PULSE: {pulse_times}')

    # Calculate Heart Rates (HR) for epochs or overall
    hr = len(pulse_times) / (max(tbasis) / 60)  # Beats per minute

    # Calculate Interbeat Intervals (IBI)
    ibi = np.diff(pulse_times)
    ibi_mean = np.mean(ibi)
    ibi_std = np.std(ibi)

    return hr, ibi, ibi_mean, ibi_std

