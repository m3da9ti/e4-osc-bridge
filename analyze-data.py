import argparse
import numpy as np

def analyze_event_type(events, event_type, event_label):
    # Filter only event_type events
    filtered_events = [x for x in events if x[1] == event_type]
    # Calculate the average gsr value
    values = [x[2][0] for x in filtered_events]
    print(f"{event_label} Mean:", np.mean(values))
    print(f"{event_label} Std:", np.std(values))
    print(f"{event_label} Min:", np.min(values))
    print(f"{event_label} Max:", np.max(values))
    # Calculate the 0.02 percentile
    print(f"{event_label} 2th Percentile:", np.percentile(values, 2))
    # Calculate the 0.98 percentile
    print(f"{event_label} 98th Percentile:", np.percentile(values, 98))
    print("--------------")


def analyze_file(filename):
    log_file = open(filename, 'r')
    events = []
    for line in log_file:
        line = line.strip()
        event_time, event_type, *sample = line.split(",")
        event_time = float(event_time)
        sample = [float(x) for x in sample]
        events.append((event_time, event_type, sample))
    events.sort(key=lambda x: x[0])

    analyze_event_type(events, "acc", "Accelerometer")
    analyze_event_type(events, "bvp", "BVP")
    analyze_event_type(events, "gsr", "GSR")
    analyze_event_type(events, "temp", "Temperature")




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Calculate statistics over the data.')
    parser.add_argument('log_file', type=str, help='Existing log file')
    args = parser.parse_args()

    print(args.log_file)
    analyze_file(args.log_file)
