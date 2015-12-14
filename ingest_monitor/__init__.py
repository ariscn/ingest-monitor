from ._version import get_versions

__author__ = 'Aris Pikeas'
__email__ = 'aris.pikeas@vizio.com'
__version__ = get_versions()['version']


import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())
