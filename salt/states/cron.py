'''
Manage cron states
'''

def present(name,
        user='root',
        minute='*',
        hour='*',
        daymonth='*',
        month='*',
        dayweek='*',
        ):
    '''
    Verifies that the specified cron job is present for the specified user
    '''
    ret = {'name': name,
           'result': True,
           'changes': {},
           'comment': ''}
    data = __salt__['cron.set_job'](
            user,
            minute,
            hour,
            daymonth,
            month,
            dayweek,
            name,
            )
    if data == 'present':
        ret['comment'] = 'Cron {0} already present'.format(name)
        return ret
    if data == 'new':
        ret['comment'] = 'Cron {0} added to {1}\'s crontab'.format(name, user)
        ret['changes'] = {user: name}
        return ret
    if data == 'updated':
        ret['comment'] = 'Cron {0} updated'.format(name, user)
        ret['changes'] = {user: name}
        return ret
    ret['comment'] = 'Cron {0} for user {1} failed to commit with error \n{2}'.format(
            name,
            user,
            data
            )
    ret['result'] = False
    return ret

def absent(name,
        user='root',
        minute='*',
        hour='*',
        daymonth='*',
        month='*',
        dayweek='*',
        ):
    '''
    Verifies that the specified cron job is absent for the specified user
    '''
    ret = {'name': name,
           'result': True,
           'changes': {},
           'comment': ''}
    data = __salt__['cron.rm_job'](
            user,
            minute,
            hour,
            daymonth,
            month,
            dayweek,
            name,
            )
    if data == 'absent':
        ret['comment'] = 'Cron {0} already absent'.format(name)
        return ret
    if data == 'removed':
        ret['comment'] = 'Cron {0} removed from {1}\'s crontab'.format(
                name,
                user
                )
        ret['changes'] = {user: name}
        return ret
    ret['comment'] = 'Cron {0} for user {1} failed to commit with error \n{2}'.format(
            name,
            user,
            data
            )
    ret['result'] = False
    return ret
