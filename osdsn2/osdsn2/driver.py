import logging
import faker
import time

from keystoneauth1.identity import v3
from keystoneauth1 import session
from novaclient import client as nova_client
from glanceclient import client as glance_client
from osdsn2 import input
from osdsn2 import exceptions

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)


class OSDriverException(Exception):
    pass


class OSDriver(object):
    UPDATE_INTERVAL = 0.250
    TIMEOUT = 140
    GENERIC_WAIT = "__GEN_WAIT__"
    MAX_TIMES_ON_TASK_COMPLETION = 5
    MAX_SECONDS_ON_TASK_COMPLETION = 5

    def __init__(self, compute_client, image_client, image_data):
        self._compute_client = compute_client
        self._image_client = image_client
        self._image_data = image_data
        self._created_flavors = []
        self._created_servers = []
        self._created_images = []
        self._server_running = None
        self._max_waiting = 0
        self._max_waiting_use = None
        self._update_list = []

    def is_server_running(self):
        return self._server_running is not None

    def _run_input_internal(self, inp):
        inp.visited = True

        flavor = None
        image = None

        if inp.name == 'resize' or inp.name == 'build':
            flavor = self.create_new_flavor(inp)
        if inp.name == 'rebuild' or inp.name == 'build':
            image = self.create_new_image(inp)

        if inp.name == 'build':
            if not self.is_server_running():
                self.create_new_server(flavor, image)

                self.wait_for_inp(inp, expect_exception='deleted' in [w.lower() for w in inp.waits if w])
                inp.used = True
            else:
                LOGGER.warning("An attempt to create two instances")
                raise OSDriverException("DuplicatedInstanceException")
        elif self.is_server_running():
            if inp.name == 'rebuild':
                self._compute_client.servers.rebuild(self._server_running, image=image)
            elif inp.name == 'pause':
                self._compute_client.servers.pause(self._server_running)
            elif inp.name == 'unpause':
                self._compute_client.servers.unpause(self._server_running)
            elif inp.name == 'shelve':
                self._compute_client.servers.shelve(self._server_running)
            elif inp.name == 'unshelve':
                self._compute_client.servers.unshelve(self._server_running)
            elif inp.name == 'reboot':
                self._compute_client.servers.reboot(self._server_running)
            elif inp.name == 'reset':
                self._compute_client.servers.reset_state(self._server_running)
            elif inp.name == 'start':
                self._compute_client.servers.start(self._server_running)
            elif inp.name == 'delete':
                self._compute_client.servers.delete(self._server_running)
                self._server_running = None
            elif inp.name == 'suspend':
                self._compute_client.servers.suspend(self._server_running)
            elif inp.name == 'resume':
                self._compute_client.servers.resume(self._server_running)
            elif inp.name == 'resize':
                self._compute_client.servers.resize(self._server_running, flavor=flavor)
            elif inp.name == 'confirm':
                self._compute_client.servers.confirm_resize(self._server_running)
            elif inp.name == 'revert':
                self._compute_client.servers.revert_resize(self._server_running)
            elif inp.name == 'shutoff':
                self._compute_client.servers.stop(self._server_running)

            self.wait_for_inp(inp, expect_exception='deleted' in [w.lower() for w in inp.waits])

            inp.used = True
        else:
            LOGGER.warning("An attempt to run an inopportune input: " + inp.name)
            raise OSDriverException("InopportuneCommandException")

    def run_input(self, inp):
        self._update_list = []
        try:
            LOGGER.info('Run %r', inp)
            self._run_input_internal(inp)
        except TimeoutError as e:
            if self.GENERIC_WAIT in inp.waits:
                inp.used = True
                inp.waits = self._update_list
            else:
                raise e
        except OSDriverException as e:
            if self.GENERIC_WAIT in inp.waits:
                inp.conflicting = True
                inp.fault_message = str(e)
                inp.waits = self._update_list
            else:
                raise e
        except exceptions.ResourceNotFound as e:
            if self.GENERIC_WAIT in inp.waits:
                inp.used = True
                inp.fault_message = str(e)
                inp.waits = self._update_list
            else:
                raise e
        except Exception as e:
            if self.GENERIC_WAIT in inp.waits:
                inp.conflicting = True
                inp.fault_message = str(e)
                inp.waits = self._update_list
            else:
                raise e
        finally:
            LOGGER.info('Ran %r', inp)

    def create_new_flavor(self, inp):
        flavor = self._compute_client.flavors.create(name=faker.Faker().first_name().lower(),
                                                   vcpus=inp.args['vcpus'],
                                                   ram=inp.args['memory'],
                                                   disk=0)
        self._created_flavors.append(flavor)
        return flavor

    def create_new_image(self, unused_input):
        image = self._image_client.images.create(name=faker.Faker().first_name().lower(),
                                                 disk_format='qcow2',
                                                 container_format='bare',
                                                 visibility='public')
        self._created_images.append(image)

        with open(self._image_data, 'rb') as img_data:
            self._image_client.images.upload(image_id=image.id,
                                             image_data=img_data)

        self.wait_until(predicate=lambda image_id: self._image_client.images.get(image_id).status == 'active',
                        args=(image.id,), update_callback=lambda image_id: self._image_client.images.get(image_id)
                        .status.lower())

        return image

    def create_new_server(self, flavor, image):
        server = self._compute_client.servers.create(name=faker.Faker().first_name().lower(),
                                                     flavor=flavor,
                                                     image=image)
        self._created_servers.append(server)
        self._server_running = server
        return server

    def wait_until(self, predicate, args, update_callback=None, ensure_task_completion=False,
                   input_timeout=None):
        times = 0
        start_time = time.time()
        timeout = self._max_waiting_use if self._max_waiting_use is not None else self.TIMEOUT
        timeout = timeout if input_timeout is None else input_timeout
        current_update = update_callback(*args) if update_callback else None
        last_update = current_update
        if current_update:
            LOGGER.info('Wait update # status %s', current_update)
            self._update_list.append(current_update)
        while not predicate(*args) and times < self.MAX_TIMES_ON_TASK_COMPLETION:
            while time.time() - start_time < timeout and not predicate(*args):
                time.sleep(self.UPDATE_INTERVAL)
                current_update = update_callback(*args) if update_callback else None
                if current_update != last_update:
                    last_update = current_update
                    LOGGER.info('Wait update # status %s', current_update)
                    self._update_list.append(current_update)
            # BEGIN CHANGE _RANDOM_ (this was not tested well yet)
            if not ensure_task_completion:
                break
            LOGGER.warning(f"Updating by {self.MAX_SECONDS_ON_TASK_COMPLETION} secs...")
            loop_time = time.time()
            while time.time() - loop_time < self.MAX_TIMES_ON_TASK_COMPLETION:
                time.sleep(self.UPDATE_INTERVAL)
                current_update = update_callback(*args) if update_callback else None
                if current_update != last_update:
                    last_update = current_update
                    LOGGER.info('Wait update plus # status %s', current_update)
                    self._update_list.append(current_update)
            times += 1
            # END CHANGE _RANDOM_
        if time.time() - start_time > self._max_waiting:
            self._max_waiting = time.time() - start_time
            LOGGER.info('Max waiting update # %is', self._max_waiting)
        if time.time() - start_time < timeout:
            LOGGER.info('Wait terminated in %is', time.time() - start_time)
        else:
            LOGGER.error('Wait timeout # elapsed %is, timeout %is', time.time() - start_time, timeout)
            raise TimeoutError()

    def set_max_waiting_use(self, max_waiting_use):
        self._max_waiting_use = max_waiting_use
        LOGGER.info('Max waiting set to %s', max_waiting_use)

    def get_max_waiting(self):
        return self._max_waiting

    def wait_for_inp(self, inp, expect_exception=False):
        waits = [wait.lower() for wait in inp.waits if wait]
        try:
            self.wait_until(predicate=lambda: getattr(self._compute_client.servers.get(self._server_running),
                                                      'OS-EXT-STS:task_state', None) is None, args=(),
                            update_callback=lambda: getattr(self._compute_client.servers.get(self._server_running),
                                                            'OS-EXT-STS:task_state', None),
                            ensure_task_completion=True, input_timeout=inp.timeout_p1)
            time.sleep(1)
            self.wait_until(predicate=lambda ws: self._compute_client.servers.get(self._server_running)
                            .status.lower() in ws, args=(waits,), update_callback=lambda _: self._compute_client
                            .servers.get(
                self._server_running
            ).status.lower(), input_timeout=inp.timeout_p2)
        except TimeoutError as e:
            self.monitor_for_faults()
            raise e
        except nova_client.exceptions.NotFound as e:
            raise exceptions.ResourceNotFound() from e
        except Exception as e:
            if expect_exception:
                LOGGER.warning('Wait inp expects for exception "%s"', str(e))
            else:
                raise e

    def monitor_for_faults(self):
        if self._server_running is None:
            return
        try:
            server = self._compute_client.servers.get(self._server_running)
            if hasattr(server, 'fault'):
                LOGGER.error(server.fault)
        except Exception as e:
            LOGGER.warning(e)

    def delete_created_resources(self):
        self.delete_flavors()
        self.delete_images()
        self.delete_servers()
        LOGGER.info('Created resources deleted')

    def delete_flavors(self):
        for flavor in self._created_flavors:
            try:
                self._compute_client.flavors.delete(flavor)
            except Exception as e:
                LOGGER.warning('Could not delete flavor %s: %s', flavor.id, str(e))
        self._created_flavors = []

    def delete_images(self):
        for image in self._created_images:
            try:
                self._image_client.images.delete(image_id=image.id)
            except Exception as e:
                LOGGER.warning('Could not delete image %s: %s', image.id, str(e))
        self._created_images = []

    def delete_servers(self):
        for server in self._created_servers:
            try:
                self._compute_client.servers.delete(server)
            except Exception as e:
                LOGGER.warning('Could not delete server %s: %s', server.id, str(e))
        self._created_servers = []
        self._server_running = None


def example_osdriver():
    auth = v3.Password(auth_url='http://localhost/identity/v3',
                       username='admin',
                       password='supersecret',
                       user_domain_id='default',
                       project_domain_id='default',
                       project_name='admin')
    ss = session.Session(auth=auth)
    compute_client = nova_client.Client(session=ss, version='2')
    image_client = glance_client.Client(session=ss, version='2')
    osdriver = OSDriver(compute_client, image_client, 'resources/cirros0.4.0.img')
    return osdriver


def main():
    osdriver = example_osdriver()
    try:
        osdriver.run_input(input.Input('build', {'vcpus': 1, 'memory': 256}, ['active'], None))
        osdriver.run_input(input.Input('pause', None, ['paused'], None))
        osdriver.run_input(input.Input('unpause', None, ['active'], None))
        osdriver.run_input(input.Input('shelve', None, ['shelved_offloaded'], None))
        osdriver.run_input(input.Input('unshelve', None, ['active'], None))
        osdriver.run_input(input.Input('reboot', None, ['active'], None))
        osdriver.run_input(input.Input('rebuild', None, ['active'], None))
        osdriver.run_input(input.Input('suspend', None, ['suspended'], None))
        osdriver.run_input(input.Input('resume', None, ['active'], None))
        osdriver.run_input(input.Input('shutoff', None, ['shutoff'], None))
        osdriver.run_input(input.Input('start', None, ['active'], None))
        osdriver.run_input(input.Input('resize', {'memory': 64, 'vcpus': 1}, ['verify_resize'], None))
        osdriver.run_input(input.Input('confirm', None, ['active'], None))
        osdriver.run_input(input.Input('shutoff', None, ['shutoff'], None))
        osdriver.run_input(input.Input('resize', {'vcpus': 1, 'memory': 256}, ['verify_resize'], None))
        osdriver.run_input(input.Input('revert', None, ['shutoff'], None))
        osdriver.run_input(input.Input('start', None, ['active'], None))
        osdriver.run_input(input.Input('reset', None, ['error'], None))
        osdriver.run_input(input.Input('delete', None, ['deleted'], None))
    finally:
        osdriver.delete_created_resources()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    main()
