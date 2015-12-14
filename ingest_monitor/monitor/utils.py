import logging

from datetime import datetime
from time import sleep


def run_forever(fn, log=None, update_interval=60*5, max_update_duration=60*1, stateful=False):
    log = log or logging.getLogger(__name__)
    state = {}
    try:
        while True:
            start = datetime.now()

            log.info('Updating...')
            try:
                if stateful:
                    state = fn(**state)
                else:
                    fn()
            except Exception as e:
                if isinstance(e, KeyboardInterrupt):
                    raise
                else:
                    log.exception('Unexpected error during update')

            elapsed = (datetime.now() - start).total_seconds()

            if elapsed > max_update_duration:
                log.error("Update check took %s seconds, max allowed is %s", elapsed, max_update_duration)

            if update_interval != 0:
                sleep_time = update_interval - (elapsed % update_interval)
                log.info("Finished update, sleeping for %.1fs.", sleep_time)
                sleep(sleep_time)

    except KeyboardInterrupt:
        log.info('Received interrupt, exiting.')
