import sys
import os
import subprocess
import shlex


def sh(cmd):
    print('+', cmd)
    subprocess.run(cmd, shell=True, check=True)


def main():
    [repo] = sys.argv[1:]

    arch = (
        subprocess.check_output('uname -m', shell=True)
        .decode('latin1')
        .strip()
    )
    if arch == 'aarch64':
        arch = 'arm64'

    vars = {
        'github': 'https://github.com/liquidinvestigations/factory',
        'repo': shlex.quote(repo),
        'arch': arch,
        'image': (
            'https://jenkins.liquiddemo.org/job/liquidinvestigations/'
            'job/factory/job/master/lastSuccessfulBuild/artifact/'
            'cloud-{}-image.tar.gz'
            .format(arch)
        ),
    }

    sh('git clone {github} {repo}'.format(**vars))
    sh('mkdir -p {repo}/images/cloud-{arch}'.format(**vars))
    os.chdir('{repo}/images/cloud-{arch}'.format(**vars))
    sh('wget --progress=dot:giga {image} -O tmp.tar.gz'.format(**vars))
    sh('zcat tmp.tar.gz | tar x')
    sh('rm tmp.tar.gz')


if __name__ == '__main__':
    main()
