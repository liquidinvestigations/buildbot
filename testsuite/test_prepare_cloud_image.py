from pathlib import Path
from tempfile import TemporaryDirectory
import pytest
import factory


@pytest.fixture
def run_factory(monkeypatch):
    with TemporaryDirectory() as tmp:
        repo = Path(tmp)
        (repo / 'images').mkdir()
        monkeypatch.setattr(factory, 'repo', repo)
        yield factory.main


def test_prepare_cloud_image(run_factory):
    run_factory(['prepare-cloud-image'])

    with TemporaryDirectory() as tmp:
        shared = Path(tmp)
        hello = shared / 'hello'
        with hello.open('w', encoding='utf8') as f:
            f.write('#!/bin/sh\ntouch /mnt/shared/world.txt\n')
        hello.chmod(0o755)

        run_factory([
            'run',
            '--share', '{}:/mnt/shared'.format(shared),
            '/mnt/shared/hello',
        ])

        assert (shared / 'world.txt').is_file()
