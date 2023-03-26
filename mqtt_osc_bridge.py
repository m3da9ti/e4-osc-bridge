import argparse
import json
import sys
import time
import traceback
from datetime import datetime as dt

import paho.mqtt.client as mqtt
from pythonosc.udp_client import SimpleUDPClient

import events
from influx import Influx

VALID_TYPES = ['acc', 'bvp', 'temp', 'gsr', 'tag']

osc_stream = False

def on_subscribe(client, userdata, mid, qos, tmp=None):
    if isinstance(qos, list):
        qos_msg = str(qos[0])
    else:
        qos_msg = f"and granted QoS {qos[0]}"
    print(dt.now().strftime("%H:%M:%S.%f")[:-2] + " Subscribed " + qos_msg)


def on_mqtt_message(client, userdata, message, tmp=None):
    """
    {
        "type": "bvp|acc|... etc",
        "device": "device id",
        "run": "run tag e.g. series-202303011422",
        "timestamp": "unix timestamp",
        "value": 01.01,

        // in case of acc:
        "x": 99,
        "y": 199,
        "z": 299
    }
    """
    decoded_msg = str(message.payload.decode("utf-8"))
    if not args.quiet:
         print("received message: ", decoded_msg)
    res = json.loads(decoded_msg)
    osc_client = None

    if osc_stream:
        osc_client = SimpleUDPClient(args.osc_ip, args.osc_port)

    if res.get('type') == 'temp':
        events.temperature_event(res, osc_client, influx, args.quiet)
    elif res.get('type') == 'bvp':
        events.bvp_event(res, osc_client, influx, args.quiet)
    elif res.get('type') == 'acc':
        events.accelerometer_event(res, osc_client, influx, args.quiet)
    elif res.get('type') == 'gsr':
        events.gsr_event(res, osc_client, influx, args.quiet)
    elif res.get('type') == 'tag':
        events.tag_event(res, osc_client, influx, args.quiet)


def on_mqtt_connect(client, userdata, flags, rc, v5config=None):
    if rc == 0:
        client.connected_flag = True
        print("connected OK Returned code=", rc)
    else:
        print("Bad connection Returned code= ", rc)


def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    print('>>>>>> stopping')
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    sys.exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Forward E4 app / mqtt messages to OSC.')
    parser.add_argument('--osc-ip', type=str, help='OSC server IP address', default='127.0.0.1')
    parser.add_argument('--osc-port', type=int, help='OSC server port', default=8000)
    parser.add_argument('--mqtt-broker', type=str, help='IP Address of MQTT Broker', default='127.0.0.1')
    parser.add_argument('--mqtt-topic', type=str, help='MQTT Topic', default='e4')
    parser.add_argument('--influx-url', type=str, help='Influx URL', default='http://localhost:8086/')
    parser.add_argument('--influx-token', type=str, help='Influx token', default='bKZ6u51oPb3rvWCskPuDWGxR39qiTVosCdUcKmsRxYWhRwYjgVNQajL7668HgAEMDlfCr9dwrxEF2QEpmV0KQQ==')
    parser.add_argument('--influx-bucket', type=str, help='Influx bucket', default='e4-bucket')
    parser.add_argument('--influx-org', type=str, help='Influx Org ID', default='230dc0ec1d83e595')
    parser.add_argument('--type', type=str, help='Filters the event type, separated by commas (e.g. bvp, gsr)',
                        default=None)

    # options not requiring values:
    # if --osc-stream is not passed from the command line, it will be False == no streaming
    parser.add_argument('--osc-stream', action='store_true', help='Stream events over osc')
    # if --record is not passed from the command line, it will be False == not saving to db
    parser.add_argument('--record', action='store_true', help='Persist all events into Influx DB')
    # if --quiet is not passed from the command line, it will be False == verbose
    parser.add_argument('--quiet', action='store_true', help='Don\'t log out all events')




    influx = None
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


    # check if we have to osc stream
    if args.osc_stream:
        print(f'Streaming to osc {args.osc_ip}:{args.osc_port}')
    osc_stream = args.osc_stream

    # connect to Influxdb if --record is given
    if args.record:
        print(f'Connecting to InfluxDB: {args.influx_url}|{args.influx_org}|{args.influx_bucket}')
        influx = Influx(args.influx_url, args.influx_token, args.influx_org, args.influx_bucket)
    
    # connect to mqtt
    mqtt.Client.connected_flag = False
    mqtt_client = mqtt.Client("osc-bridge", transport='tcp', protocol=mqtt.MQTTv5)
    print(f'Connecting to mqtt broker at: {args.mqtt_broker}')

    # mqtt callbacks
    mqtt_client.on_connect = on_mqtt_connect
    mqtt_client.on_subscribe = on_subscribe
    mqtt_client.on_message = on_mqtt_message

    from paho.mqtt.properties import Properties
    from paho.mqtt.packettypes import PacketTypes

    properties = Properties(PacketTypes.CONNECT)
    properties.SessionExpiryInterval = 30 * 60  # in seconds

    try:
        mqtt_client.connect(args.mqtt_broker,
                       port=1883,
                       clean_start=mqtt.MQTT_CLEAN_START_FIRST_ONLY,
                       properties=properties,
                       keepalive=60
                       )

        print(f'>>>> subscribing to the mqtt topic ... {args.mqtt_topic}')
        mqtt_client.subscribe(args.mqtt_topic)

        time.sleep(10)

        print(f'>>>> starting the mqtt loop...')
        mqtt_client.loop_forever()

        # print(f'>>>> setting the signal')
        # signal.signal(signal.SIGINT, signal_handler)
    except KeyboardInterrupt:
        print('Ctrl-C is pressed, stopping the mqtt loop...')
        mqtt_client.loop_stop()
        print('disconnecting...')
        mqtt_client.disconnect()

    except Exception:
        traceback.print_exc()
