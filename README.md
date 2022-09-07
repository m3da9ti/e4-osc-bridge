# Empatica E4 - OSC bridge

This Python script receives messages from the Empatica E4 streaming server and forwards them to OSC.

It uses [open-e4-client](https://pypi.org/project/open-e4-client/) and [Python OSC](https://pypi.org/project/python-osc/) to communicate with both the E4 and OSC.

# Setup

- Install Python 3.

- Install dependencies:
```
pip install open-e4-client python-osc
```
- Run the script with the correct arguments. To see a list of arguments, run:

```
python e4-osc-bridge.py --help
```
- E.g. to provide a different OSC port and address, write:

```
python e4-osc-bridge.py --osc_ip 192.168.1.5 --osc_port 9999
```


