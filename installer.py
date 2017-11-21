import sys
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
    sh('mkdir -p images/cloud-{arch}'.format(**vars))
    sh('cd images/cloud-{arch}; '
       'wget -q {image} -O tmp.tar.xz; '
       'xzcat tmp.tar.xz | tar x; '
       'rm tmp.tar.xz'.format(**vars))


if __name__ == '__main__':
    main()
