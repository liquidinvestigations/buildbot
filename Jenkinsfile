stage('Build Image') {
    parallel cloud: {
        node('cloud') {
            checkout scm
            try {

                sh 'git clone https://github.com/liquidinvestigations/setup.git shared/setup'
                sh '''
                echo "liquid_domain: liquid.jenkins-build.example.org" > ./shared/setup/ansible/vars/config.yml
                echo "devel: true" >> ./shared/setup/ansible/vars/config.yml
                '''

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
            try {
                sh 'git clone https://github.com/liquidinvestigations/setup.git shared/setup'
                sh '''
                echo "liquid_domain: liquid.jenkins-build.example.org" > ./shared/setup/ansible/vars/config.yml
                echo "devel: true" >> ./shared/setup/ansible/vars/config.yml
                '''

                sh './prepare_cloud_image.py'
                sh './buildbot run shared/setup/bin/build_image odroid_c2'
            }
            finally {
                    archive 'shared/ubuntu-odroid_c2-raw.img'
                    deleteDir()
            }
        }
    }
}
