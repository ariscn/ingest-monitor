import logging
log = logging.getLogger(__name__)

from collections import defaultdict
from datetime import datetime

from peewee import CharField, DateTimeField, IntegerField, UpdateQuery

from ..extensions import DB


class Channel(DB.Model):
    class Meta:
        db_table = 'Channels'

    GOOD_SIGNAL = 1
    BAD_CONTENT_ID = 'None'

    content_id = CharField(db_column='ContentID')
    hostname = CharField()
    ip_address = CharField(db_column='IpAddress')
    name = CharField(db_column='Channel')
    last_update = DateTimeField(db_column='LastUpdate')
    signal = IntegerField()

    def __str__(self):
        return "%s / %s" % (self.name, self.hostname)

    @property
    def is_down(self):
        return self.signal != self.GOOD_SIGNAL

    def is_stale(self, max_update_age=60*3, check_time=None):
        elapsed = (check_time or datetime.now()) - self.last_update
        return elapsed.total_seconds() > max_update_age

    @property
    def is_missing_content_id(self):
        return self.content_id == self.BAD_CONTENT_ID

    def get_alarms_types(self, check_time=None):
        alarm_types = []

        if self.is_missing_content_id:
            alarm_types.append(ALARM_MISSING_CONTENT_ID)
        if self.is_down:
            alarm_types.append(ALARM_BAD_SIGNAL)
        if self.is_stale(check_time):
            alarm_types.append(ALARM_NO_UPDATE)

        return alarm_types


ALARM_MISSING_CONTENT_ID = 0
ALARM_BAD_SIGNAL = 1
ALARM_NO_UPDATE = 2

_ALARM_TYPE__NAME = {
    ALARM_MISSING_CONTENT_ID: 'ALARM_MISSING_CONTENT_ID',
    ALARM_BAD_SIGNAL: 'ALARM_BAD_SIGNAL',
    ALARM_NO_UPDATE: 'ALARM_NO_UPDATE',
}

_ALARM_NAME__TYPE = {
    'ALARM_MISSING_CONTENT_ID': ALARM_MISSING_CONTENT_ID,
    'ALARM_BAD_SIGNAL': ALARM_BAD_SIGNAL,
    'ALARM_NO_UPDATE': ALARM_NO_UPDATE,
}


class Alarm(DB.Model):
    class Meta:
        db_table = 'Alarms'

    type = IntegerField(db_column='AlarmType')
    start = DateTimeField(db_column='AlarmSet')
    end = DateTimeField(db_column='AlarmClear')

    active = IntegerField()
    channel_name = CharField(db_column='Channel')
    source = CharField()

    @staticmethod
    def type_to_name(type):
        return _ALARM_TYPE__NAME[type]

    @classmethod
    def select_with_channels(cls):
        return cls.select(cls, Channel).join(Channel, on=(Channel.name == cls.channel_name).alias('channel'))

    @classmethod
    def add_sources(cls):
        for alarm in cls.select_with_channels():
            # Roundtrip to the DB for each update, but this is a one-shot function anyway.
            cls.update(source=alarm.channel.ip_address).where(cls.id == alarm.id).execute()

    # @classmethod
    # def open_alarms(cls):
    #     return cls.select().where(cls.end.is_null(False))

    @classmethod
    def get_grouped_open(cls):
        alarms = defaultdict(list)
        for alarm in cls.select_with_channels().where(cls.end.is_null(False)):
            alarms[alarm.type].append(alarm.channel)

        return alarms

    @classmethod
    def close_expired(cls, check_time=None):
        check_time = check_time or datetime.now()
        expired_ids = []
        for alarm in cls.select_with_channels().where(cls.end.is_null(False)):
            if alarm.is_expired(check_time):
                log.info("Alarm %s expired, closing...", alarm)
                expired_ids.append(alarm.id)

        UpdateQuery(cls, end=check_time).where(cls.id.in_(expired_ids)).execute()

    @property
    def is_expired(self, check_time=None):
        return (
            (self.type == ALARM_BAD_SIGNAL and not self.channel.is_down) or
            (self.type == ALARM_MISSING_CONTENT_ID and not self.channel.is_missing_content_id) or
            (self.type == ALARM_NO_UPDATE and not self.channel.is_stale(check_time))
        )
