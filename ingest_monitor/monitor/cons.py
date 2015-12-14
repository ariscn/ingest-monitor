import logging
log = logging.getLogger(__name__)

from datetime import datetime
from json import load
from os import environ
from sys import stdin

from consul import Consul, Check
from pygerduty import PagerDuty
from slacker import Slacker

from .utils import run_forever
from ..models import Channel


consul = Consul(
    host=environ['CONSUL_IP'],
    token=environ.get('CONSUL_TOKEN', None),
    dc=environ.get('CONSUL_DC', None),
)


CHECKS = (
    ('signal', 'Signal', '300s'),
    ('content-id', 'Content ID', '300s'),
    ('update', 'Update', '300s'),
)


#pagerduty = PagerDuty(environ['PAGERDUTY_SUBDOMAIN'], environ['PAGERDUTY_API_TOKEN'])
slack = Slacker(environ['SLACK_API_TOKEN'])


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


def check_to_slack(check, channel=environ['SLACK_CHANNEL'], bot='ingest'):
    text = "%s / %s is now: %s" % (check['Name'], check['ServiceID'], check['Status'])
    log.debug(text)
    slack.chat.post_message(channel, text, username=bot)


def check_to_pagerduty(check):
    pass


def alert(last_checks=None):
    last_checks = last_checks or {}
    checks = {}

    for id, check in consul.agent.checks().items():
        if id not in last_checks:
            log.info("New check registered: %s", check['CheckID'])
            last_checks[id] = check

        checks[id] = check

        if (not check['ServiceID'].startswith('ingest')) or (last_checks[id]['Status'] == check['Status']):
            continue

        check_to_slack(check)
        check_to_pagerduty(check)

    return {'last_checks': checks}


def alert_forever():
    log.info('Consul alert updater started')
    run_forever(alert, log=log, update_interval=60, max_update_duration=60)


def test():
    checks = [c for c in load(stdin) if c['ServiceName'].startswith('ingest')]
    print('foo')
