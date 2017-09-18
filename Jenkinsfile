// vim: ft=groovy
parallel cloud: {
    node('cloud') {
        deleteDir()
        checkout scm
        try {
            stage('CLOUD: Setup the setup repo') {
                sh './setup_setup'
            }
            stage('CLOUD: Prepare Cloud Image') {
                sh './prepare_cloud_image.py'
            }
            stage('CLOUD: Build Image') {
                sh './buildbot run shared/setup/bin/build_image cloud'
            }
        }

        finally {
            stage('CLOUD: Archive Raw Image') {
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
            stage('ODROID C2: Setup the setup repo') {
                sh './setup_setup'
            }
            stage('ODROID C2: Prepare Cloud Image') {
                sh './prepare_cloud_image.py'
            }
            stage('ODROID C2: Build Image') {
                sh './buildbot run shared/setup/bin/build_image odroid_c2'
            }
        }
        finally {
            stage('ODROID C2: Archive Raw Image') {
                archive 'shared/ubuntu-odroid_c2-raw.img'
            }
        }
    }
}
