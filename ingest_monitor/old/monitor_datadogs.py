#!/usr/bin/python

from sets import Set
from datetime import datetime
import requests
import time
import os
from sendmail import MailSender
import statsd

stats = statsd.StatsClient(host='10.164.46.219', port=8125, prefix=None)

CHECK_INTERVAL = 60 * 15

BASE_DIR=os.path.dirname(os.path.realpath(__file__))

channel_list = []
status_list = []

sendemail = False

"""
"""
def get_channels():
    global channel_list
    with open(BASE_DIR + "/channels.csv", "rU") as f:
        channel_list = []
        lines = f.readlines()
        for c in lines:
            channel = c.strip('\n')
            channel_list.append(channel)

"""
"""
def get_dd_status():
    global status_list

    with open(BASE_DIR + "/datadogs.csv", "rU") as f:
        status_list = []
        lines = f.readlines()
        for dd in lines:
            dd = dd.strip('\n')
            url = "http://{0}/?cmd=status".format(dd)
            try:
                out = requests.get(url)
                if out.status_code == 200:
                    items=eval(out.content)
                    for item in items:
                       contents = item[1].split("_")
                       cid = contents[0]
                       channel = contents[1]
                       points1 = item[2]
                       points2 = item[3]

                       item = {'channel':channel, 'cid': cid, 'points1':points1, 'points2':points2}

                       if channel == 'INFOMERCIAL':
                           continue
                       if points1 == 0 and points2 == 0:
                           continue

                       status_list.append(item)
            except:
                 print "Cannot connect to {0}".format(dd)

def SendEmail(subject, body):
    if sendemail is True:
        sender = MailSender("smtp.gmail.com", 587, "vahid@kowsari.com", "online6809")
        sender.SendMail("vahid@cognitivenetworks.com", ["vahid@kowsari.com","vahid@cognitivenetworks.com"], subject, body)


if __name__ == "__main__":
    get_channels()
    subject = "Monitoring Datadogs started"
    body = "" 
    SendEmail(subject, body)

    while True:
        now = datetime.utcnow()
        print "Checking {0}".format(now.strftime("%Y-%m-%d %H:%M:%S"))

        get_dd_status()

        print "Channels currenty ingesting {0}".format(len(status_list))
        print "{0}".format(sorted([x['channel'] for x in status_list]))
        stats.gauge("ingest.channels.count_from_datadogs", len(status_list))

        print "Channels should be ingesting {0}".format(len(channel_list))
	channel_set = Set(channel_list)
	status_set = Set([x['channel'] for x in status_list])

	missing = channel_set.difference(status_set)
        missing_list = ", ".join(sorted([i for i in missing]))
	print "Missing {0} {1} ".format(len(missing), missing_list)

	extra = status_set.difference(channel_set)
        extra_list = ", ".join(sorted([i for i in extra]))
	print "Extra {0} {1} ".format(len(extra), extra_list)

        if len(missing) > 0:
            subject = "Missing Channels"
            body = missing_list
            SendEmail(subject, body)

        if len(extra) > 0:
            subject = "Extra Channels"
            body = extra_list
            SendEmail(subject, body)

	time.sleep(CHECK_INTERVAL)
