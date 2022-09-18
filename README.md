# Empatica E4 - OSC bridge

This Python script receives messages from the Empatica E4 streaming server and forwards them to OSC.

It uses [open-e4-client](https://pypi.org/project/open-e4-client/) and [Python OSC](https://pypi.org/project/python-osc/) to communicate with both the E4 and OSC.

# Setup

- Install Python 3.

- Install dependencies:
```
pip install open-e4-client python-osc
```

# Usage

## Recording an E4 event stream

Connect to an E4 Streaming Server, read all events, record them in an event log and forwards them over OSC:

```
python e4-osc-bridge.py --record event.log --osc_ip 192.168.1.5 --osc_port 9999
```

## Replaying an E4 event stream

Read events from a recorded log file and forward them over OSC, using the correct timing:

```
python e4-osc-bridge.py --osc_ip 192.168.1.5 --osc_port 9999
```

## Additional options

To see a list of arguments, run:

```
python e4-osc-bridge.py --help
```
