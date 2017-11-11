def write(path, content, mode=0o755):
    with path.open('w', encoding='utf8') as f:
        f.write(content)
    path.chmod(mode)


def test_run_touch(factory):
    write(factory.shared / 'hello', '#!/bin/sh\ntouch /mnt/shared/world.txt\n')

    factory.main([
        'run',
        '--share', '{}:/mnt/shared'.format(factory.shared),
        '/mnt/shared/hello',
    ])

    assert (factory.shared / 'world.txt').is_file()
