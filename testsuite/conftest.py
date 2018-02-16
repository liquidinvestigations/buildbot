import sys
import subprocess
from contextlib import contextmanager
from tempfile import TemporaryDirectory
from pathlib import Path
import threading
import pytest

repo = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(repo)]

import factory as factory_module  # noqa

default_paths = factory_module.paths


def pytest_addoption(parser):
    parser.addoption('--image', help="use existing image for tests")


@contextmanager
def monkeypatcher():
    from _pytest.monkeypatch import MonkeyPatch
    mocks = MonkeyPatch()
    try:
        yield mocks
    finally:
        mocks.undo()


@contextmanager
def thread(target):
    t = threading.Thread(target=target)
    t.start()
    yield
    t.join()


@contextmanager
def tmpdir_factory():
    with TemporaryDirectory() as tmp:
        tmp_repo = Path(tmp)

        with monkeypatcher() as mocks:

            class FactoryWrapper:

                def __init__(self):
                    self.images = tmp_repo / 'images'
                    self.images.mkdir()

                    tmp_paths = factory_module.Paths(tmp_repo)
                    mocks.setattr(factory_module, 'paths', tmp_paths)
                    self.main = factory_module.main

                    self.ssh_input = b''
                    mocks.setattr(
                        factory_module.VM,
                        'invoke_ssh',
                        self.invoke_ssh,
                    )

                def invoke_ssh(self, command):
                    self.ssh_result = subprocess.run(
                        command,
                        input=self.ssh_input,
                        stdout=subprocess.PIPE,
                        timeout=120,
                        check=True,
                    )


            yield FactoryWrapper()


@pytest.fixture(scope='session')
def cloud_image(pytestconfig):
    image_name = pytestconfig.getoption('--image')

    if image_name:
        yield default_paths.IMAGES / image_name

    else:
        with tmpdir_factory() as factory:
            factory.main(['prepare-cloud-image'])
            [image] = factory.images.iterdir()
            yield image


@pytest.fixture
def factory(cloud_image):
    with tmpdir_factory() as factory:
        (factory.images / cloud_image.name).symlink_to(cloud_image)
        yield factory


@pytest.fixture
def shared():
    with TemporaryDirectory() as tmp:
        yield Path(tmp)
