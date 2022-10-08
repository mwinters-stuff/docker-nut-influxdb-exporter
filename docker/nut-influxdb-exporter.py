#!/usr/bin/python3
import os
import time
import traceback

from nut2 import PyNUTClient
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS

# InfluxDB details
INFLUX_BUCKET = None
INFLUX_ORG = None
INFLUX_TOKEN = None
INFLUX_URL = None
HOSTNAME = 'localhost'

NUT_HOST = None
NUT_PORT = None
NUT_PASSWORD = None
NUT_USERNAME = None
NUT_WATTS = None
INTERVAL = None
UPS_NAME = None
VERBOSE = None


REMOVE_KEYS = ['driver.version.internal', 'driver.version.usb',
               'ups.beeper.status', 'driver.name', 'battery.mfr.date']
TAG_KEYS = ['battery.type', 'device.model', 'device.serial', 'driver.version', 'driver.version.data',
            'device.mfr', 'device.type', 'ups.mfr', 'ups.model', 'ups.productid', 'ups.serial', 'ups.vendorid']


def convert_to_type(s):
    """ A function to convert a str to either integer or float. If neither, it will return the str. """
    try:
        int_var = int(s)
        return int_var
    except ValueError:
        try:
            float_var = float(s)
            return float_var
        except ValueError:
            return s


def construct_object(data, remove_keys, tag_keys):
    """
    Constructs NUT data into  an object that can be sent directly to InfluxDB

    :param data: data received from NUT
    :param remove_keys: some keys which are considered superfluous
    :param tag_keys: some keys that are actually considered tags and not measurements
    :return:
    """
    fields = {}
    tags = {'host': HOSTNAME}

    for k, v in data.items():
        if k not in remove_keys:
            if k in tag_keys:
                tags[k] = v
            else:
                fields[k] = convert_to_type(v)

    watts = float(NUT_WATTS) if NUT_WATTS else float(
        fields['ups.realpower.nominal'])
    fields['watts'] = watts * 0.01 * fields['ups.load']

    result = [
        {
            'measurement': 'ups_status',
            'fields': fields,
            'tags': tags
        }
    ]
    return result


def main_loop():
    # Main infinite loop: Get the data from NUT every interval and send it to InfluxDB.
    while True:
        print("Connecting to InfluxDB url:{}".format(INFLUX_URL))
        try:
            iclient = influxdb_client.InfluxDBClient(
                url=INFLUX_URL,
                token=INFLUX_TOKEN,
                org=INFLUX_ORG
            )

            if iclient:
                # print("Connected successfully to InfluxDB")

                write_api = iclient.write_api(write_options=SYNCHRONOUS)

                # print("Connecting to NUT host {}:{}".format(NUT_HOST, NUT_PORT))
                ups_client = PyNUTClient(host=NUT_HOST, port=NUT_PORT, login=NUT_USERNAME, password=NUT_PASSWORD, debug=VERBOSE)
                if ups_client:
                    # print("Connected successfully to NUT")

                    ups_data = ups_client.list_vars(UPS_NAME)

                    json_body = construct_object(ups_data, REMOVE_KEYS, TAG_KEYS)

                    # print(json_body)
                    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=json_body)
                    ups_client = None
                iclient.close()
                iclient = None
        except:
            tb = traceback.format_exc()
            print(tb)
            print("Error.")
            exit(1)


        time.sleep(INTERVAL)


if __name__ == '__main__':
    if os.environ.get('INFLUX_BUCKET'):
        INFLUX_BUCKET = os.environ.get('INFLUX_BUCKET')
    if os.environ.get('INFLUX_ORG'):
        INFLUX_ORG = os.environ.get('INFLUX_ORG')
    if os.environ.get('INFLUX_TOKEN'):
        INFLUX_TOKEN = os.environ.get('INFLUX_TOKEN')
    if os.environ.get('INFLUX_URL'):
        INFLUX_URL = os.environ.get('INFLUX_URL')

    HOSTNAME = os.getenv('HOSTNAME', 'localhost')

    # NUT related variables
    NUT_HOST = os.getenv('NUT_HOST', '127.0.0.1')
    NUT_PORT = os.getenv('NUT_PORT') if os.getenv('NUT_PORT') != '' else '3493'
    NUT_PASSWORD = os.getenv('NUT_PASSWORD') if os.getenv(
        'NUT_PASSWORD') != '' else None
    NUT_USERNAME = os.getenv('NUT_USERNAME') if os.getenv(
        'NUT_USERNAME') != '' else None
    NUT_WATTS = os.getenv('WATTS') if os.getenv('WATTS') != '' else None
    # Other vars
    INTERVAL = float(os.getenv('INTERVAL', 21))
    UPS_NAME = os.getenv('UPS_NAME', 'UPS')
    VERBOSE = os.getenv('VERBOSE', 'false').lower() == 'true'

    if not INFLUX_BUCKET or not INFLUX_ORG or not INFLUX_TOKEN or not INFLUX_URL:
        print("Provide environment")
        exit(1)

    if VERBOSE:
        print("INFLUX_BUCKET: ", INFLUX_BUCKET)
        print("INFLUX_TOKEN: ", INFLUX_TOKEN)
        print("INFLUX_URL: ", INFLUX_URL)
        print("INFLUX_ORG: ", INFLUX_ORG)
        print("NUT_USER: ", NUT_USERNAME)
        # print("NUT_PASS: ", nut_password)
        print("UPS_NAME", UPS_NAME)
        print("INTERVAL: ", INTERVAL)
        print("VERBOSE: ", VERBOSE)

    main_loop()
