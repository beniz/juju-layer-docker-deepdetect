import os
import shutil

from subprocess import check_call

from charmhelpers.core import hookenv
from charmhelpers.core import unitdata
from charmhelpers.fetch import install_remote

from charms import reactive
from charms.reactive import hook
from charms.reactive import when
from charms.reactive import when_not

db = unitdata.kv()
config = hookenv.config()


@hook('config-changed')
def config_changed():
    '''
    On every config changed hook execution, check for password changes - if the
    password has changed, we need to force stop the container and re-execute.
    '''
    #if config.changed('password'):
    #    stop_container()
    # clone_repository()
    ##TODO: port change
    

@when('docker.available')
def install_deepdetect():
    '''
    Default to only pulling the image once. A forced upgrade of the image is
    planned later. Updating on every run may not be desireable as it can leave
    the service in an inconsistent state.
    '''
    if reactive.is_state('deepdetect.available'):
        return
    hookenv.status_set('maintenance', 'Pulling DeepDetect image')
    check_call(['docker', 'pull', 'beniz/deepdetect_cpu'])
    reactive.set_state('deepdetect.available')


@when('deepdetect.available', 'docker.available')
@when_not('deepdetect.started')
def run_container(port=8080):
    '''
    Wrapper method to launch a docker container under the direction of Juju,
    and provide feedback/notifications to the end user.
    '''
    ##TODO: options, such as port etc...
#    if not password:
#        password = config.get('password')
    # Run the ipython docker container.
    hookenv.status_set('maintenance', 'Stopping DeepDetect container')
    # make this cleaner
    try:
        check_call(['docker', 'stop', 'docker-deepdetect'])
    except:
        pass
    try:
        check_call(['docker', 'rm', 'docker-deepdetect'])
    except:
        pass
    run_command = [
        'docker',
        'run',
        '--name',
        'docker-deepdetect',
        '-p',
        '{}:8080'.format(config.get('port')),
        '-d',
        'beniz/deepdetect_cpu'
    ]
    check_call(run_command)
    hookenv.open_port(config.get('port'))  # want you to open this port in cloud firewall
    reactive.remove_state('deepdetect.stopped')
    reactive.set_state('deepdetect.started')
    hookenv.status_set('active', 'DeepDetect container started')


@when('deepdetect.stop', 'docker.available') # status = at juju level (user sees this)
@when_not('deepdetect.stopped') # state
def stop_container():
    '''
    Stop the DeepDetect application container, remove it, and prepare for launching
    of another application container so long as all the config values are 
    appropriately set.
    '''
    hookenv.status_set('maintenance', 'Stopping DeepDetect container')
    # make this cleaner
    try:
        check_call(['docker', 'stop', 'docker-deepdetect'])
    except:
        pass
    try:
        check_call(['docker', 'rm', 'docker-deepdetect'])
    except:
        pass
    reactive.remove_state('deepdetect.started')
    reactive.remove_state('deepdetect.stop')
    reactive.set_state('deepdetect.stopped')
    hookenv.status_set('waiting', 'DeepDetect container stopped')


@when('deepdetect.started', 'deepdetect.available')
def configure_website_port(http):
    '''
    Relationship context, used in tandem with the http relation stub to provide
    an ip address (default to private-address) and set the port for the
    relationship data
    '''
    serve_port = config.get('port')
    http.configure(port=serve_port)
    hookenv.status_set('active', '')


# def clone_repository(branch='master'):
#     '''
#     Wrapper method around charmhelpers.install_remote to handle fetching of a
#     vcs url to deploy a static website for use in the iPython container.
#     '''
#     repo_dir = None

#     if config.get('repository'):
#         hookenv.status_set('maintenance', 'Cloning repository')

#         if not config.changed('repository'):
#             repo_dir = db.get('repo_dir')

#         repo_dir = install_remote(config.get('repository'), dest=config.get('webroot'),
#                                   branch=branch, depth=None)
#         db.set('repo_dir', repo_dir)
#         stop_container()
#         run_container(repo_dir)
#         hookenv.status_set('active', '')
