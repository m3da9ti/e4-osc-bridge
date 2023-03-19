import influxdb_client
from influxdb_client.client.write_api import WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS, ASYNCHRONOUS
import pandas as pd

class Influx:
    def __init__(self, url, token, org, bucket='e4-bucket'):
        self.client = influxdb_client.InfluxDBClient(url, token, org)
        self.org = org
        self.bucket = bucket
        self.write_api = self.client.write_api() # write_options=SYNCHRONOUS 
        self.query_api = self.client.query_api()

    def write_to_influx(self, sensor, device_uid, run_tag, timestamp, value, x=None, y=None, z=None):
        p = influxdb_client.Point(sensor)
        p.tag("device_id", device_uid)
        p.tag("run_tag", run_tag)
        p.time(timestamp, WritePrecision.MS)
        if value:
            p.field("reading", value)
        else:
            p.field("x", x)
            p.field("y", y)
            p.field("z", z)

        self.write_api.write(bucket=self.bucket, org=self.org, record=p)
        print(p, flush=True)

    def read_from_influx(self, device_id, run_tag, bucket='e4-bucket', event_types=None):
        query = f'''from(bucket:"{bucket}")
                |> range(start: -365d)
                |> filter(fn: (r) => r.device_id == "Empatica E4 - {device_id}")
                |> filter(fn: (r) => r.run_tag == "{run_tag}")'''
        
        # if event_types:
        #         query = query + f'''
        #         |> filter(fn:(r) => r._measurement == "my_measurement")
        #         '''

        records = []
        # results_df = self.query_api.query_data_frame(org=self.org, query=query)
        results = self.query_api.query(org=self.org, query=query)
        # print(f'@@@@@ {results_df.head()}')

        for table in results:
            for record in table.records:
                records.append((record.get_field(), record.get_value()))
                print(f'@@@@@ {record}')
                break
            break