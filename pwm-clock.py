# SPDX-FileCopyrightText: 2020 John Furcean
# SPDX-License-Identifier: MIT

import time, rtc
import board
import feathers2
import ipaddress
import ssl
import wifi
import socketpool
import adafruit_requests

from digitalio import DigitalInOut, Direction, Pull
import pulseio

# OFFSETS for my panel meters so the dial starts at 0
# it takes some tweaking to get them to align just right
# you could also play with their physical orientation as well
HOUR_OFFSET = 700
MIN_OFFSET = 2200
SEC_OFFSET = 500
RTC_CLOCK = rtc.RTC()


def sync_rtc():
    '''
    Reteives time from worldtimeapi.org
    Sets RTC_CLOCK
    Modified from: https://gist.github.com/dglaude/29666db218eadae3aa5e0ec0999ad51b
    '''
    status_code = 0

    while status_code != 200:
        print("https://worldtimeapi.org/api/timezone/%s"%secrets["timezone"])
        response = requests.get("https://worldtimeapi.org/api/timezone/%s"%secrets["timezone"])
        #response = requests.get("http://worldtimeapi.org/api/timezone/CET")
        status_code = response.status_code
        print(status_code)
        print(response)

    datetime_str = response.json()['datetime']
    #print(datetime_str)
    datesplit = datetime_str.split("-")
    year = int(datesplit[0])
    month = int(datesplit[1])
    timesplit = datesplit[2].split("T")
    mday = int(timesplit[0])
    timesplit = timesplit[1].split(":")
    hours = int(timesplit[0])
    minutes = int(timesplit[1])
    seconds = int(float(timesplit[2].split("-")[0]))
    RTC_CLOCK.datetime =  time.struct_time((year, month, mday, hours, minutes, seconds, 0, 0, False))


# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

print("Connecting to %s"%secrets["ssid"])
wifi.radio.connect(secrets["ssid"], secrets["password"])
print("Connected to %s!"%secrets["ssid"])
print("My IP address is", wifi.radio.ipv4_address)

# Test and debug Connection
ipv4 = ipaddress.ip_address("8.8.4.4")
print("Ping google.com: %f ms" % wifi.radio.ping(ipv4))
 
pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())


# initialize the 3v panel meters
analog_hours = pulseio.PWMOut(board.A3, frequency=5000, duty_cycle=0)
analog_minutes = pulseio.PWMOut(board.A4, frequency=5000, duty_cycle=0)
analog_seconds = pulseio.PWMOut(board.A5, frequency=5000, duty_cycle=0)

# set the panel meters to zero (0) based on their offsets
# (this could be different for everyone)
analog_hours.duty_cycle = HOUR_OFFSET
analog_minutes.duty_cycle = MIN_OFFSET
analog_seconds.duty_cycle = SEC_OFFSET

# initialize hours, minutes and seconds to 0
# this forces a sync on the intial loop
hours = 0
minutes = 0
seconds = 0

while True:

    # sync the clock on intitial loop and every 4 hours
    if (hours%4, minutes, seconds) == (0,0,0):
        
        print("\nSyncing Clock...\n")
        sync_rtc()

    hours = (RTC_CLOCK.datetime.tm_hour % 12)
    minutes = RTC_CLOCK.datetime.tm_min
    seconds = RTC_CLOCK.datetime.tm_sec



    print("%02d:%02d:%02d" % (hours, minutes, seconds))

    # calculate the location for each panel meter
    analog_seconds.duty_cycle = int(SEC_OFFSET+seconds*(60500/60))
    analog_minutes.duty_cycle = int(MIN_OFFSET+minutes*(60500/60))
    analog_hours.duty_cycle = int(HOUR_OFFSET+hours*(60500/12))

