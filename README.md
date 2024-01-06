# Empatica E4 - OSC bridge

This Python script receives messages from the MQTT broker and can forward them to OSC and/or save/store into InfluxDB

It uses [Python OSC](https://pypi.org/project/python-osc/) to communicate with OSC.

# Setup

- Install Python 3.

- Install dependencies:
```
pip3 install -r requirements.txt
```

# Usage

## Recording an E4 event stream

Connect to an MQTT (topuc = 'e4'), read all events, store them in InfluxDB and forward them over OSC:

```
python3 mqtt_osc_bridge.py --record --osc-port 8000 --osc-stream
 ```

## Replaying an E4 event stream

Read events from InfluxDB for a specific run by supplying its ID and forward them over OSC, using the correct timing:

```
python3 influxdb_replay.py --run-tag series-031920231413 --osc_ip 192.168.1.5 --osc_port 9999
```

## Additional options

To see a list of arguments, run:

```
python3 <script name> --help
```
