import logging
log = logging.getLogger(__name__)

from os import environ

from .connections import consul, pagerduty, slack
from .utils import run_forever


def check_to_slack(check, channel=environ['SLACK_CHANNEL'], bot='ingest'):
    text = "%s / %s is now: %s" % (check['Name'], check['ServiceID'], check['Status'])
    log.debug(text)
    slack.chat.post_message(channel, text, username=bot)


def check_to_pagerduty(check, service_key=environ['PAGERDUTY_SERVICE_KEY']):
    kwargs = {
        'service_key': service_key,
        'incident_key': check['CheckID']
    }
    kwargs['event_type'] = 'trigger' if check['Status'] == 'critical' else 'resolve'
    if kwargs['event_type'] == 'trigger':
        kwargs['description'] = check['Name']
        kwargs['details'] = check

    pagerduty.create_event(**kwargs)


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

        try:
            check_to_slack(check)
            check_to_pagerduty(check)
        except:
            log.exception('Unexpected error while sending alerts.')

    return {'last_checks': checks}


def alert_forever():
    log.info('Consul alert updater started')
    run_forever(alert, log=log, update_interval=60, max_update_duration=60, stateful=True)

