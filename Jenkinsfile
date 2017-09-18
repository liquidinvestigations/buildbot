// vim: ft=groovy
parallel cloud: {
    node('cloud') {
        deleteDir()
        checkout scm
        try {
            stage('Setup the setup repo') {
                sh './setup_setup'
            }
            stage('Prepare Cloud Image') {
                sh './prepare_cloud_image.py'
            }
            stage('Build Cloud Image') {
                sh './buildbot run shared/setup/bin/build_image cloud'
            }
        }

        finally {
            stage('Archive raw Cloud Image') {
                archive 'shared/ubuntu-x86_64-raw.img'
            }
        }
    }
},
odroid_c2: {
    node('odroid_c2') {
        deleteDir()
        checkout scm
        try {
            stage('Setup the setup repo') {
                sh './setup_setup'
            }
            stage('Prepare Cloud Image') {
                sh './prepare_cloud_image.py'
            }
            stage('Build Odroid C2 Image') {
                sh './buildbot run shared/setup/bin/build_image odroid_c2'
            }
        }
        finally {
            stage('Archive raw Odroid C2 Image') {
                archive 'shared/ubuntu-odroid_c2-raw.img'
            }
        }
    }
}
