import logging
log = logging.getLogger(__name__)

from ast import literal_eval
from time import sleep, time
from os import environ

from requests import get, RequestException


def get_channels(filename=environ['CHANNEL_FILE']):
    with open(filename) as file:
        channels = [c.strip('\n') for c in file.readlines()]

    return channels


def get_dd_statuses(filename=environ['DATADOG_FILE']):
    with open(filename) as file:
        datadogs = file.read().splitlines()

    statuses = []
    for dd in datadogs:
        try:
            res = get("http://%s/?cmd=status" % dd)
            res.raise_for_status()
        except RequestException:
            log.warning("Cannot connect to %s", dd)
            continue

        log.debug("Response from %s: %s", dd, res.content)
        for _, status, p1, p2 in literal_eval(res.content.decode('utf-8')):
            cid, channel, _ = status.split('_')

            if channel == 'INFOMERCIAL' or (p1 == p2 == 0):
                continue

            statuses.append({'channel': channel, 'cid': cid, 'points1': p1, 'points2': p2})

    return statuses


def get_channel_diffs():
    channels = set(get_channels())
    live_channels = set(s['channel'] for s in get_dd_statuses())
    return (channels - live_channels, live_channels - channels)


def run_forever(update_interval=60*15, max_update_duration=60):
    log.info('Datadog monitor started')

    try:
        while True:
            log.info('Updating...')
            start = time()

            missing, extras = get_channel_diffs()

            if missing:
                log.error("Missing channels not present on datadogs: %s", ', '.join(missing))
            if extras:
                log.warning("Extra channels on datadogs: %s", ', '.join(extras))

            elapsed = time() - start
            if elapsed > max_update_duration:
                log.error("Update check took %s seconds, max allowed is %s", elapsed, max_update_duration)

            sleep_time = update_interval - ((time() - start) % update_interval)
            log.info("Finished update, sleeping for %.1fs.", sleep_time)
            sleep(sleep_time)
    except KeyboardInterrupt:
        log.info('Received interrupt, exiting.')
