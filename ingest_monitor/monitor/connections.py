from os import environ

from consul import Consul
from pygerduty import PagerDuty
from slacker import Slacker


consul = Consul(
    host=environ['CONSUL_IP'],
    token=environ.get('CONSUL_API_TOKEN', None),
    dc=environ.get('CONSUL_DC', None),
)

pagerduty = PagerDuty(environ['PAGERDUTY_SUBDOMAIN'], environ['PAGERDUTY_API_TOKEN'])

slack = Slacker(environ['SLACK_API_TOKEN'])
