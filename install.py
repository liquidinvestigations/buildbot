import os
import subprocess
import shlex
import argparse


def sh(cmd):
    print('+', cmd)
    subprocess.run(cmd, shell=True, check=True)


def main():
    arch = (
        subprocess.check_output('uname -m', shell=True)
        .decode('latin1')
        .strip()
    )
    if arch == 'aarch64':
        arch = 'arm64'

    default_image = (
        'https://jenkins.liquiddemo.org/job/liquidinvestigations/'
        'job/factory/view/change-requests/job/PR-32/lastSuccessfulBuild/artifact/'
        'xenial-{}.factory.gz'
        .format(arch)
    )

    parser = argparse.ArgumentParser()
    parser.add_argument('repo')
    parser.add_argument('--image', default=default_image)
    options = parser.parse_args()

    vars = {
        'github': 'https://github.com/liquidinvestigations/factory',
        'repo': shlex.quote(options.repo),
        'arch': arch,
        'image': options.image,
    }

    sh('git clone {github} {repo}'.format(**vars))
    os.chdir(vars['repo'])
    sh('wget --progress=dot:giga {image} -O tmp.factory.gz'.format(**vars))
    sh('zcat tmp.factory.gz | ./factory import cloud-{arch}'.format(**vars))
    sh('rm tmp.factory.gz')


if __name__ == '__main__':
    main()
