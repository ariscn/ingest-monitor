import logging
log = logging.getLogger(__name__)

from datetime import datetime

from peewee import ForeignKeyField, BooleanField, CharField, DateTimeField, UpdateQuery

from ..extensions import DB


class ServerType(DB.Model):
    name = CharField()


class Server(DB.Model):
    type = ForeignKeyField(ServerType)

    hostname = CharField()
    ip_address = CharField()


class Source(DB.Model):
    callsign = CharField()

    def __str__(self):
        return str(self.callsign)


class IngestStream(DB.Model):
    source = ForeignKeyField(Source)
    server = ForeignKeyField(Server)

    def __str__(self):
        return "%s-%s" % (self.source_id, self.server_id)


class IngestStreamStatus(DB.Model):
    stream = ForeignKeyField(IngestStream)

    content_id = CharField()
    signal = BooleanField()
    timestamp = DateTimeField(default=datetime.now)


class IngestStreamAlarmType(DB.Model):
    name = CharField()


class IngestStreamAlarm(DB.Model):
    type = ForeignKeyField(IngestStreamAlarmType)
    status = ForeignKeyField(IngestStreamStatus)

    start = DateTimeField(default=datetime.now)
    end = DateTimeField(null=True)

    pagerduty_incident_key = CharField(null=True)

    @classmethod
    def close_expired(cls, check_time=None):
        check_time = check_time or datetime.now()
        expired_ids = []
        for alarm in cls.select(cls, Source).where(cls.end.is_null()):
            if alarm.is_expired(check_time):
                log.info("Alarm %s expired, closing...", alarm)
                expired_ids.append(alarm.id)

        UpdateQuery(cls, end=check_time).where(cls.id.in_(expired_ids)).execute()


