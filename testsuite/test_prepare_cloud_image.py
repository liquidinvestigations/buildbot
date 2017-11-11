def test_run_touch(factory):
    hello = factory.shared / 'hello'
    with hello.open('w', encoding='utf8') as f:
        f.write('#!/bin/sh\ntouch /mnt/shared/world.txt\n')
    hello.chmod(0o755)

    factory.main([
        'run',
        '--share', '{}:/mnt/shared'.format(factory.shared),
        '/mnt/shared/hello',
    ])

    assert (factory.shared / 'world.txt').is_file()
