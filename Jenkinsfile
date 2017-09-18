// vim: ft=groovy ts=4 sw=4 et
stage('Build Image') {
    parallel cloud: {
        node('cloud') {
            checkout scm
            try {
                sh './setup_setup'
                sh './prepare_cloud_image.py'
                sh './buildbot run shared/setup/bin/build_image cloud'

            }

            finally {
                archive 'shared/ubuntu-x86_64-raw.img'
                deleteDir()
            }
        }
    },
    odroid_c2: {
        node('odroid_c2') {
            checkout scm
            try {
                sh './setup_setup'
                sh './prepare_cloud_image.py'
                sh './buildbot run shared/setup/bin/build_image odroid_c2'
            }
            finally {
                archive 'shared/ubuntu-odroid_c2-raw.img'
                deleteDir()
            }
        }
    },
    failFast: false
}
