import logging
log = logging.getLogger(__name__)

from datetime import datetime

from .utils import run_function_forever

from ..models import DB, Alarm, Channel


NOTIFICATION_TYPE = 'TODO'


# def SendAlarmNotification(i, body):
#     if "email" in NOTIFICATION_TYPE:
#         SendEmail("Server {0}({1}) Channel: {2} Ingest Alarm".format(i['Hostname'], i['IPAddress'], i['Channel']), body)

# def SendAlarmClearedNotification(i, body):
#     if "email" in NOTIFICATION_TYPE:
#         SendEmail("Server {0}({1}) Channel: {2} Ingest Alarm Cleared".format(i['Hostname'], i['IPAddress'], i['Channel']), body)


# def AlarmTypeToString(a):
#     values = ['Content ID Null', 'No Signal', 'No Updates']
#     return values[a]

# def AlarmsToString(i):
#     alarms=""
#     if (i is not None):
#         for a in i.keys():
#            alarms = alarms + "Type {0} {1} ".format(AlarmTypeToString(int(a)), i[a])
#     return alarms



# def LogMessage(subject, body):
#     if "email" in NOTIFICATION_TYPE:
#        SendEmail(subject, body)


def refresh(check_time=None):
    check_time = check_time or datetime.now()

    with DB.atomic():
        alarms = {(a.type, a.channel_name, a.source): a for a in Alarm.get_open_alarms()}

        fresh_alarms = []
        for channel in Channel.select():
            for alarm_type in channel.get_alarm_types(check_time):
                if (alarm_type, channel.name, channel.hostname) in alarms:
                    msg = 'already open'
                else:
                    msg = 'opening new alarm...'

                    fresh_alarms.append({
                        'channel_name': channel.name,
                        'source': channel.hostnam,
                        'type': alarm_type,
                        'start': check_time,
                    })
                log.info("Alarm %s / %s: %s", channel, Alarm.type_to_name(alarm_type), msg)

        Alarm.close_expired(check_time=check_time)
        Alarm.insert_many(fresh_alarms)


def run_forever(update_interval=60*15, max_update_duration=60):
    log.info('Channel monitor started')
    run_function_forever(refresh, log, update_interval, max_update_duration)


    # for i in channellist:
    #     if (len(alarms_set) > 0):
    #         body = ""
    #         channels = ""
    #         for j in alarms_set.keys():
    #             body += "Location: {0} Server: {1} ({2}) Channel: {3} Alarm: {4}'\n".format(i['Location'], i['Hostname'], i['IPAddress'], i['Channel'], AlarmTypeToString(int(j)))
    #             channels += i['Channel'] + " "
    #         SendAlarmNotification(i, body)
    #         logger.info(body)

    #     if (len(alarms_clear) > 0):
    #         body = ""
    #         channels = ""
    #         for j in alarms_clear.keys():
    #             #timediff = alarms_clear[j] - i['Alarms'][j]
    #             body += "Location: {0} Server: {1} ({2}) Channel: {3} Alarm Cleared: {4} Downtime: '{5}'".format(i['Location'], i['Hostname'], i['IPAddress'], i['Channel'], AlarmTypeToString(int(j)), 0)

    #             channels += i['Channel'] + " "
    #         logger.info(body)
    #         SendAlarmClearedNotification(i, body)



