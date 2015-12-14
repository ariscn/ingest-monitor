#!/usr/bin/env python

from setuptools import find_packages, setup

import versioneer

setup(
    name='ingest-monitor',

    packages=find_packages(),
    entry_points='''
        [console_scripts]
        ingest-monitor = ingest_monitor.manage:main
        ingest-monitor-old = ingest_monitor.old.monitor:Start
    ''',
    author='Aris Pikeas',
    author_email='aris.pikeas@vizio.com',
    description='Ingest monitor',
    url='https://github.com/pikeas/ingest-monitor',

    keywords='',
    classifiers=[
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],

    cmdclass=versioneer.get_cmdclass(),
    test_suite='tests',
    version=versioneer.get_version(),
    zip_safe=False,
)
