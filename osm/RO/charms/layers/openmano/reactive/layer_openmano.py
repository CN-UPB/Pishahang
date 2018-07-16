from git import Repo as gitrepo
from shutil import rmtree

import os
import subprocess

from charmhelpers.core import host
from charmhelpers.core import hookenv
from charmhelpers.core import templating
from charmhelpers.core.unitdata import kv
from charmhelpers.core.hookenv import (
    config,
    log,
    open_port,
    status_set,
)

from charmhelpers.core.host import (
    chownr,
)

from charms.reactive import (
    when,
    when_not,
    set_state,
    is_state,
)

kvdb = kv()

INSTALL_PATH = '/opt/openmano'
USER = 'openmanod'


@when('openmano.installed', 'openmano.available')
def openmano_available(openmano):
    # TODO make this configurable via charm config
    openmano.configure(port=9090)


@when('openvim-controller.available',
      'db.available',
      'db.installed',
      'openmano.installed',
      'openmano.running',
      )
def openvim_available(openvim, db):
    for service in openvim.services():
        for endpoint in service['hosts']:
            host = endpoint['hostname']
            port = endpoint['port']
            user = endpoint['user']

            openvim_uri = '{}:{}'.format(host, port)
            if kvdb.get('openvim_uri') == openvim_uri:
                return

            # TODO: encapsulate the logic in create-datacenter.sh into python
            try:
                cmd = './scripts/create-datacenter.sh {} {} {} {}'.format(
                    host, port, user, kvdb.get('openmano-tenant'))
                out, err = _run(cmd)
            except subprocess.CalledProcessError as e:
                # Ignore the error if the datacenter already exists.
                if e.returncode != 153:
                    raise

            kvdb.set('openvim_uri', openvim_uri)
            if not is_state('db.available'):
                status_set('waiting', 'Waiting for database')
            break
        break


@when('openmano.installed',
      'db.installed',
      'openvim-controller.available')
@when_not('openmano.running')
def start(*args):
    # TODO: if the service fails to start, we should raise an error to the op
    # Right now, it sets the state as running and the charm dies. Because
    # service-openmano returns 0 when it fails.
    cmd = "/home/{}/bin/service-openmano start".format(USER)
    out, err = _run(cmd)

    if not kvdb.get('openmano-tenant'):
        out, err = _run('./scripts/create-tenant.sh')
        kvdb.set('openmano-tenant', out.strip())

    status_set(
        'active',
        'Up on {host}:{port}'.format(
            host=hookenv.unit_public_ip(),
            port='9090'))

    set_state('openmano.running')


@when('db.available', 'openmano.installed')
@when_not('db.installed')
def setup_db(db):
    """Setup the database

    """
    db_uri = 'mysql://{}:{}@{}:{}/{}'.format(
        db.user(),
        db.password(),
        db.host(),
        db.port(),
        db.database(),
    )

    if kvdb.get('db_uri') == db_uri:
        # We're already configured
        return

    status_set('maintenance', 'Initializing database')

    try:
        # HACK: use a packed version of init_mano_db until bug https://osm.etsi.org/bugzilla/show_bug.cgi?id=56 is fixed
        # cmd = "{}/database_utils/init_mano_db.sh --createdb ".format(kvdb.get('repo'))
        cmd = "./scripts//init_mano_db.sh --createdb "
        cmd += "-u {} -p{} -h {} -d {} -P {}".format(
            db.user(),
            db.password(),
            db.host(),
            db.database(),
            db.port(),
        )
        output, err = _run(cmd)
    except subprocess.CalledProcessError:
        # Eat this. init_mano_db.sh will return error code 1 on success
        pass

    context = {
        'user': db.user(),
        'password': db.password(),
        'host': db.host(),
        'database': db.database(),
        'port': db.port(),
    }
    templating.render(
        'openmanod.cfg',
        os.path.join(kvdb.get('repo'), 'openmanod.cfg'),
        context,
        owner=USER,
        group=USER,
    )
    kvdb.set('db_uri', db_uri)

    status_set('active', 'Database installed.')
    set_state('db.installed')


@when_not('openvim-controller.available')
def need_openvim():
    status_set('waiting', 'Waiting for OpenVIM')


@when_not('db.available')
def need_db():
    status_set('waiting', 'Waiting for database')


@when_not('db.available')
@when_not('openvim-controller.available')
def need_everything():
    status_set('waiting', 'Waiting for database and OpenVIM')


@when_not('openmano.installed')
def install_layer_openmano():
    status_set('maintenance', 'Installing')

    cfg = config()

    # TODO change user home
    # XXX security issue!
    host.adduser(USER, password=USER)

    if os.path.isdir(INSTALL_PATH):
        rmtree(INSTALL_PATH)

    gitrepo.clone_from(
        cfg['repository'],
        INSTALL_PATH,
        branch=cfg['branch'],
    )

    chownr(
        INSTALL_PATH,
        owner=USER,
        group=USER,
        follow_links=False,
        chowntopdir=True
    )

    os.mkdir(os.path.join(INSTALL_PATH, 'logs'))
    chownr(INSTALL_PATH, USER, USER)
    kvdb.set('repo', INSTALL_PATH)

    os.mkdir('/home/{}/bin'.format(USER))

    os.symlink(
        "{}/openmano".format(INSTALL_PATH),
        "/home/{}/bin/openmano".format(USER))
    os.symlink(
        "{}/scripts/openmano-report.sh".format(INSTALL_PATH),
        "/home/{}/bin/openmano-report.sh".format(USER))
    os.symlink(
        "{}/scripts/service-openmano.sh".format(INSTALL_PATH),
        "/home/{}/bin/service-openmano".format(USER))

    open_port(9090)
    set_state('openmano.installed')


def _run(cmd, env=None):
    if isinstance(cmd, str):
        cmd = cmd.split() if ' ' in cmd else [cmd]

    log(cmd)
    p = subprocess.Popen(cmd,
                         env=env,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    retcode = p.poll()
    if retcode > 0:
        raise subprocess.CalledProcessError(
            returncode=retcode,
            cmd=cmd,
            output=stderr.decode("utf-8").strip())
    return (stdout.decode('utf-8'), stderr.decode('utf-8'))
