def write(path, content, mode=0o755):
    with path.open('w', encoding='utf8') as f:
        f.write(content)
    path.chmod(mode)


def test_run_touch(factory):
    with TemporaryDirectory() as shared:
        factory.main([
            'run',
            '--share', '{}:/mnt/shared'.format(shared),
            'touch', '/mnt/shared/world.txt',
        ])
        assert (Path(shared) / 'world.txt').is_file()
