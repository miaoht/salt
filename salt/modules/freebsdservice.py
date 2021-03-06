'''
The service module for FreeBSD
'''

# Import python libs
import logging
import os

# Import salt libs
import salt.utils
from salt.exceptions import CommandNotFoundError


log = logging.getLogger(__name__)


def __virtual__():
    '''
    Only work on systems which default to systemd
    '''
    # Disable on these platforms, specific service modules exist:
    if __grains__['os'] == 'FreeBSD':
        return 'service'
    return False


@salt.utils.memoize
def _cmd():
    '''
    Return full path to service command
    '''
    service = salt.utils.which('service')
    if not service:
        raise CommandNotFoundError
    return service


def _get_rcscript(name):
    '''
    Return full path to service rc script
    '''
    cmd = '{0} -r'.format(_cmd())
    for line in __salt__['cmd.run_stdout'](cmd).splitlines():
        if line.endswith('{0}{1}'.format(os.path.sep, name)):
            return line
    return None


def _get_rcvar(name):
    '''
    Return rcvar
    '''
    if not available(name):
        log.error('Service {0} not found'.format(name))
        return False

    cmd = '{0} {1} rcvar'.format(_cmd(), name)

    for line in __salt__['cmd.run_stdout'](cmd).splitlines():
        if not '_enable="' in line:
            continue
        rcvar, _ = line.split('=', 1)
        return rcvar

    return None


def get_enabled():
    '''
    Return what services are set to run on boot

    CLI Example::

        salt '*' service.get_enabled
    '''
    ret = []
    service = _cmd()
    for svc in __salt__['cmd.run']('{0} -e'.format(service)).splitlines():
        ret.append(os.path.basename(svc))

    # This is workaround for bin/173454 bug
    for svc in get_all():
        if svc in ret:
            continue
        if not os.path.exists('/etc/rc.conf.d/{0}'.format(svc)):
            continue
        if enabled(svc):
            ret.append(svc)

    return sorted(ret)


def get_disabled():
    '''
    Return what services are available but not enabled to start at boot

    CLI Example::

        salt '*' service.get_disabled
    '''
    en_ = get_enabled()
    all_ = get_all()
    return sorted(set(all_) - set(en_))


def _switch(name,                   # pylint: disable-msg=C0103
            on,                     # pylint: disable-msg=C0103
            **kwargs):
    '''
    Switch on/off service start at boot.
    '''
    if not available(name):
        return False

    rcvar = _get_rcvar(name)
    if not rcvar:
        log.error('rcvar for service {0} not found'.format(name))
        return False

    config = kwargs.get('config',
                        __salt__['config.option']('service.config',
                                                  default='/etc/rc.conf'
                                                  )
                        )

    if not config:
        rcdir = '/etc/rc.conf.d'
        if not os.path.exists(rcdir) or not os.path.isdir(rcdir):
            log.error('{0} not exists'.format(rcdir))
            return False
        config = os.path.join(rcdir, rcvar.replace('_enable', ''))

    nlines = []
    edited = False

    if on:
        val = 'YES'
    else:
        val = 'NO'

    if os.path.exists(config):
        with salt.utils.fopen(config, 'r') as ifile:
            for line in ifile:
                if not line.startswith('{0}='.format(rcvar)):
                    nlines.append(line)
                    continue
                rest = line[len(line.split()[0]):]  # keep comments etc
                nlines.append('{0}="{1}"{2}'.format(rcvar, val, rest))
                edited = True
    if not edited:
        nlines.append('{0}="{1}"\n'.format(rcvar, val))

    with salt.utils.fopen(config, 'w') as ofile:
        ofile.writelines(nlines)

    return True


def enable(name, **kwargs):
    '''
    Enable the named service to start at boot

    name
        service name

    config : /etc/rc.conf
        Config file for managing service. If config value is
        empty string, then /etc/rc.conf.d/<service> used.
        See man rc.conf(5) for details.

        Also service.config variable can be used to change default.

    CLI Example::

        salt '*' service.enable <service name>
    '''
    return _switch(name, True, **kwargs)


def disable(name, **kwargs):
    '''
    Disable the named service to start at boot

    Arguments the same as for enable()

    CLI Example::

        salt '*' service.disable <service name>
    '''
    return _switch(name, False, **kwargs)


def enabled(name):
    '''
    Return True if the named servioce is enabled, false otherwise

    name
        Service name

    CLI Example::

        salt '*' service.enabled <service name>
    '''
    if not available(name):
        log.error('Service {0} not found'.format(name))
        return False

    cmd = '{0} {1} rcvar'.format(_cmd(), name)

    for line in __salt__['cmd.run_stdout'](cmd).splitlines():
        if not '_enable="' in line:
            continue
        _, state, _ = line.split('"', 2)
        return state.lower() in ('yes', 'true', 'on', '1')

    # probably will never reached
    return False


def disabled(name):
    '''
    Return True if the named servioce is enabled, false otherwise

    CLI Example::

        salt '*' service.disabled <service name>
    '''
    return not enabled(name)


def get_all():
    '''
    Return a list of all available services

    CLI Example::

        salt '*' service.get_all
    '''
    ret = []
    service = _cmd()
    for srv in __salt__['cmd.run']('{0} -l'.format(service)).splitlines():
        if not srv.isupper():
            ret.append(srv)
    return sorted(ret)


def start(name):
    '''
    Start the specified service

    CLI Example::

        salt '*' service.start <service name>
    '''
    cmd = '{0} {1} onestart'.format(_cmd(), name)
    return not __salt__['cmd.retcode'](cmd)


def stop(name):
    '''
    Stop the specified service

    CLI Example::

        salt '*' service.stop <service name>
    '''
    cmd = '{0} {1} onestop'.format(_cmd(), name)
    return not __salt__['cmd.retcode'](cmd)


def restart(name):
    '''
    Restart the named service

    CLI Example::

        salt '*' service.restart <service name>
    '''
    if name == 'salt-minion':
        salt.utils.daemonize_if(__opts__)
    cmd = '{0} {1} onerestart'.format(_cmd(), name)
    return not __salt__['cmd.retcode'](cmd)


def reload(name):
    '''
    Restart the named service

    CLI Example::

        salt '*' service.reload <service name>
    '''
    cmd = '{0} {1} onereload'.format(_cmd(), name)
    return not __salt__['cmd.retcode'](cmd)


def status(name, **kwargs):
    '''
    Return the status for a service (True or False).

    name
        Name of service.

    CLI Example::

        salt '*' service.status <service name>
    '''
    cmd = '{0} {1} onestatus'.format(_cmd(), name)
    return not __salt__['cmd.retcode'](cmd)


def available(name, **kwargs):
    '''
    Check that the given service is available.

    CLI Example::

        salt '*' service.available sshd
    '''
    return name in get_all()
