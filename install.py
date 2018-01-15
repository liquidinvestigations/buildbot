import sys
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
        'job/factory/job/master/lastSuccessfulBuild/artifact/'
        'cloud-{}-image.tar.gz'
        .format(arch)
    )

    parser = argparse.ArgumentParser()
    parser.add_argument('repo')
    parser.add_argument('--image', default=default_image)
    options = parser.parse_args()

    [repo] = sys.argv[1:]

    vars = {
        'github': 'https://github.com/liquidinvestigations/factory',
        'repo': shlex.quote(repo),
        'arch': arch,
        'image': options.image,
    }

    sh('git clone {github} {repo}'.format(**vars))
    sh('mkdir -p {repo}/images/cloud-{arch}'.format(**vars))
    os.chdir('{repo}/images/cloud-{arch}'.format(**vars))
    sh('wget --progress=dot:giga {image} -O tmp.tar.gz'.format(**vars))
    sh('zcat tmp.tar.gz | tar x')
    sh('rm tmp.tar.gz')


if __name__ == '__main__':
    main()
