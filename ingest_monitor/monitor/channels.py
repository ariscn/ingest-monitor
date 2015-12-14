import logging
log = logging.getLogger(__name__)

from datetime import datetime

from consul import Check

from .connections import consul
from .utils import run_forever
from ..models import Channel


CHECKS = (
    ('signal', 'Signal', '300s'),
    ('content-id', 'Content ID', '300s'),
    ('update', 'Update', '300s'),
)


def _service_name(channel):
    return "ingest:%s" % channel.name

def _service_id(channel):
    return "ingest:%s-%s" % (channel.name, channel.hostname)

def _check_id(channel, check_name):
    return "service:ingest:%s-%s:%s" % (channel.name, channel.hostname, check_name)


def register_channel(channel):
    service_id = _service_id(channel)

    log.info("Adding Consul service: %s", service_id)
    consul.agent.service.register(
        name=_service_name(channel),
        service_id=service_id,
        address=channel.ip_address
    )

    for check_name, description, ttl in CHECKS:
        consul.agent.check.register(
            "%s %s %s" % (channel.name, channel.hostname, description),
            check=Check.ttl(ttl),
            check_id=_check_id(channel, check_name),
            service_id=service_id
        )


def deregister_all_channels():
    for channel in Channel.select():
        consul.agent.service.deregister(_service_id(channel))


def update_consul():
    check_time = datetime.now()
    known_services = consul.agent.services()

    for channel in Channel.select():
        if _service_id(channel) not in known_services:
            register_channel(channel)

        log.info("%s: refreshing checks", channel)
        # TODO use CHECKS tuple
        if not channel.is_down:
            log.debug("%s passed signal check", channel)
            consul.agent.check.ttl_pass(_check_id(channel, 'signal'))
        if not channel.is_missing_content_id:
            log.debug("%s passed content-id check", channel)
            consul.agent.check.ttl_pass(_check_id(channel, 'content-id'))
        if not channel.is_stale(check_time=check_time):
            log.debug("%s passed update check", channel)
            consul.agent.check.ttl_pass(_check_id(channel, 'update'))


def update_forever():
    log.info('Consul channel updater started')
    run_forever(update_consul, log=log, update_interval=5, max_update_duration=60*2)
