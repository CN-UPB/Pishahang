#!/usr/bin/env python

#from distutils.core import setup
#from distutils.command.install_data import install_data
from setuptools import setup
from os import system
#import glob

_name = 'osm_ro'
_description = 'OSM Resource Orchestrator'
_author = 'ETSI OSM'
_author_email = 'alfonso.tiernosepulveda@telefonica.com'
_maintainer = 'garciadeblas'
_maintainer_email = 'gerardo.garciadeblas@telefonica.com'
_license = 'Apache 2.0'
_url = 'https://osm.etsi.org/gitweb/?p=osm/RO.git;a=summary'
_requirements = [
    "PyYAML",
    "bottle",
    #"mysqlclient",
    #"MySQLdb",
    "jsonschema",
    "paramiko",
    "argcomplete",
    "requests",
    "logutils",
    "python-openstackclient",
    "python-novaclient",
    "python-keystoneclient",
    "python-glanceclient",
    "python-neutronclient",
    "python-cinderclient",
    #"pyvcloud",
    #"progressbar",
    "prettytable",
    #"pyvmomi",
    "boto",
    #"lib_osm_openvim",
    #"osm_im",
    "pycrypto",
]

setup(name=_name,
      version_command=('git describe', 'pep440-git'),
      description = _description,
      long_description = open('README.rst').read(),
      author = _author,
      author_email = _author_email,
      maintainer = _maintainer,
      maintainer_email = _maintainer_email,
      url = _url,
      license = _license,
      packages = [_name],
      #packages = ['osm_ro', 'osm_roclient'],
      package_dir = {_name: _name},
      package_data = {_name: ['vnfs/*.yaml', 'vnfs/examples/*.yaml',
                         'scenarios/*.yaml', 'scenarios/examples/*.yaml',
                         'instance-scenarios/examples/*.yaml', 'database_utils/*',
                         'scripts/*']},
      data_files = [('/etc/osm/', ['osm_ro/openmanod.cfg']),
                   ('/etc/systemd/system/', ['osm_ro/osm-ro.service']),
                   ],
      scripts=['openmanod', 'openmano', 'osm_ro/scripts/service-openmano', 'osm_ro/scripts/openmano-report',],
      install_requires=_requirements,
      include_package_data=True,
      setup_requires=['setuptools-version-command'],
      #test_suite='nose.collector',
      )

