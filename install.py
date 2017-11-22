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
            'cloud-{}-image.tar.xz'
            .format(arch)
        ),
    }

    sh('git clone {github} {repo}'.format(**vars))
    sh('cd {repo}'.format(**vars))
    sh('mkdir -p {repo}/images/cloud-{arch}'.format(**vars))
    os.chdir('{repo}/images/cloud-{arch}'.format(**vars))
    sh('wget -q {image} -O tmp.tar.xz'.format(**vars))
    sh('xzcat tmp.tar.xz | tar x')
    sh('rm tmp.tar.xz')


if __name__ == '__main__':
    main()
