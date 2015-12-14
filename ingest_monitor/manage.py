import logging
from os import environ

from flask_script import Manager, Shell, Server
from flask_script.commands import ShowUrls#, Clean
# #from flask_migrate import MigrateCommand

from .app import create_app
from .extensions import DB
from . import models
from .monitor.cons import test


console = logging.StreamHandler()
console.setFormatter(logging.Formatter("%(asctime)s %(name)-24s %(levelname)-8s %(message)s", datefmt='%b %d %H:%M:%S'))

logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.WARN)

log = logging.getLogger('')
log.setLevel(environ.get('LOG_LEVEL', 'INFO').upper())
log.addHandler(console)


app = create_app(environ.get('FLASK_CONFIG', 'prod'))

manager = Manager(app)
# # manager.add_command('db', MigrateCommand)
# manager.add_command("clean", Clean())
manager.add_command('server', Server())
manager.add_command("urls", ShowUrls())

manager.add_command('shell', Shell(make_context=lambda: {
    'app': app,
    'DB': DB,
    'models': models,
    'Alarm': models.Alarm,
    'Channel': models.Channel,
    'IngestStreamAlarm': models.IngestStreamAlarm,
    'Source': models.Source,
    'IngestStream': models.IngestStream,
}))

@manager.command
def create_tables():
    models.ServerType.create_table()
    models.Server.create_table()
    models.Source.create_table()
    models.IngestStream.create_table()
    models.IngestStreamStatus.create_table()
    models.IngestStreamAlarmType.create_table()
    models.IngestStreamAlarm.create_table()


@manager.command
def watch_channels():
    log.debug('Channel watcher waiting for JSON on stdin...')
    test()


def main():
    manager.run()


if __name__ == '__main__':
    main()
