import string
import sys
import os.path
from datetime import datetime
from datetime import timedelta
import smtplib
from email.mime.text import MIMEText
import logging
from logging import handlers
import daemon
import lockfile
import urllib
from asq.initiators import query
import time
import atexit
import monitor
import ConfigParser

#NOTIFICATION_TYPE = os.environ['NOTIFICATION_TYPE']
#ALARM_EMAIL_FROM = os.environ['ALARM_EMAIL_FROM']
#ALARM_EMAIL_TO = os.environ['ALARM_EMAIL_TO']
#ALARM_USERNAME = os.environ['ALARM_USERNAME']
#ALARM_PASSWORD = os.environ['ALARM_PASSWORD']
#MAX_UPDATE_SEC = os.environ['MAX_UPDATE_SEC']
#CHECK_INTERVAL_SEC = os.environ['CHECK_INTERVAL_SEC']


"""
"""
def SendAlarmNotification(i, body):
    if "email" in NOTIFICATION_TYPE:
        SendEmail("Server {0}({1}) Channel: {2} Ingest Alarm".format(i['Hostname'], i['IPAddress'], i['Channel']), body)

"""
"""
def SendAlarmClearedNotification(i, body):
    if "email" in NOTIFICATION_TYPE:
        SendEmail("Server {0}({1}) Channel: {2} Ingest Alarm Cleared".format(i['Hostname'], i['IPAddress'], i['Channel']), body)

"""
"""
def SendEmail(subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = ALARM_EMAIL_FROM
    msg['To'] = ALARM_EMAIL_TO

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com',465) #port 465 or 587
        server.ehlo()
        ''' server.starttls() '''
        server.ehlo()
        server.login(ALARM_USERNAME, ALARM_PASSWORD)
        server.sendmail(ALARM_EMAIL_FROM, ALARM_EMAIL_TO, msg.as_string())
        server.close()
    except smtplib.SMTPException:
	logger.exception('Unable to send message')
	import pdb
	pdb.set_trace()

"""
"""
def AlarmTypeToString(a):
    values = ['Content ID Null', 'No Signal', 'No Updates']
    return values[a]

"""
"""
def AlarmsToString(i):
    alarms=""
    if (i is not None):
        for a in i.keys():
           alarms = alarms + "Type {0} {1} ".format(AlarmTypeToString(int(a)), i[a])
    return alarms


"""
"""
def CheckChannels():
    logger.info("Checking Channels")
    repo = monitor.Repository()
    channellist = repo.GetAllChannels()
    allalarms = repo.GetCurrentAlarms()
    for i in channellist:
        changed = 0
        alarms_set = {}
        alarms_clear = {}
        alert_msg = []

        stale_time = datetime.now() - timedelta(seconds=int(MAX_UPDATE_SEC))

        channel_alarms = [a for a in allalarms if a['Channel'] == i['Channel']]
        has_content_alarm = len([a for a in channel_alarms if a['AlarmType'] == 0] ) > 0
        has_signal_alarm = len([a for a in channel_alarms if a['AlarmType'] == 1] ) > 0
        has_update_alarm = len([a for a in channel_alarms if a['AlarmType'] == 2] ) > 0

        #print "Channel {0} Content Alarm '{1}', Signal Alarm '{2}', Update Alarm '{3}'".format(i['Channel'], has_content_alarm, has_signal_alarm, has_update_alarm)

        if (i['ContentID'] == "None" and not has_content_alarm):
            alert_msg.append("Channel {0} - No Content!".format(i['Channel']))
            alarms_set['0'] = datetime.now()
        elif (i['ContentID'] != "None" and has_content_alarm):
            alarms_clear['0'] = datetime.now()

        if (i['Signal'] != 1 and not has_signal_alarm):
            alert_msg.append("Channel {0} - No Signal!".format(i['Channel']))
            alarms_set['1'] = datetime.now()
        elif (i['Signal'] == 1 and has_signal_alarm):
            alarms_clear['1'] = datetime.now()

        last_update = datetime.strptime(i['LastUpdate'], '%Y-%m-%d %H:%M:%S.%f')
        if (last_update < stale_time and not has_update_alarm):
            alert_msg.append("Channel {0} - No update since {1}".format(i['Channel'], i['LastUpdate']))
            alarms_set['2'] = datetime.now()
        elif (last_update > stale_time and has_update_alarm):
            alarms_clear['2'] = datetime.now()

        # set the alert if it wasnt set
        if (len(alarms_set) > 0):
            body = ""
            channels = ""
            for j in alarms_set.keys():
                body += "Location: {0} Server: {1} ({2}) Channel: {3} Alarm: {4}'\n".format(i['Location'], i['Hostname'], i['IPAddress'], i['Channel'], AlarmTypeToString(int(j)))
                channels += i['Channel'] + " "
            SendAlarmNotification(i, body)
            logger.info(body)
            changed = 1

        # clear the alert if it was set and now it is resolved
        if (len(alarms_clear) > 0):
            body = ""
            channels = ""
            for j in alarms_clear.keys():
                #timediff = alarms_clear[j] - i['Alarms'][j]
                body += "Location: {0} Server: {1} ({2}) Channel: {3} Alarm Cleared: {4} Downtime: '{5}'".format(i['Location'], i['Hostname'], i['IPAddress'], i['Channel'], AlarmTypeToString(int(j)), 0)

                channels += i['Channel'] + " "
            logger.info(body)
            SendAlarmClearedNotification(i, body)
            changed = 1

        if (changed):
           repo.UpdateAlarms(i['Channel'], alarms_set, alarms_clear)
    logger.info("Done checking")

def LogMessage(subject, body):
    if "email" in NOTIFICATION_TYPE:
       SendEmail(subject, body)

def AtExit():
    logger.info("Montoring exited")
    LogMessage("Montoring exited", "Monitoring exited")

def Start():
    logger.info("Starting...")
    LogMessage("Montoring Started", "Monitoring started")

    while (1):
       CheckChannels()
       time.sleep(float(CHECK_INTERVAL_SEC))


if __name__ == '__main__':
    logger = logging.getLogger('log')
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
    logger.addHandler(handler)

    config = ConfigParser.ConfigParser()
    config_file = os.path.dirname(os.path.realpath(__file__)) + "/ingestmonitor.ini"
    logger.info("Reading Config file {0}".format(config_file))
    config.read(config_file)

    NOTIFICATION_TYPE = config.get('settings', 'NOTIFICATION_TYPE')
    ALARM_EMAIL_FROM = config.get('settings', 'ALARM_EMAIL_FROM')
    ALARM_EMAIL_TO = config.get('settings', 'ALARM_EMAIL_TO')
    ALARM_USERNAME = config.get('settings', 'ALARM_USERNAME')
    ALARM_PASSWORD = config.get('settings', 'ALARM_PASSWORD')
    MAX_UPDATE_SEC = config.get('settings', 'MAX_UPDATE_SEC')
    CHECK_INTERVAL_SEC = config.get('settings', 'CHECK_INTERVAL_SEC')

    Start()
    asdfasdf
