pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                sh 'echo "Starting configuring and x86 build..."'
                sh './prepare_cloud_image.py'
                sh 'git clone https://github.com/liquidinvestigations/setup.git shared/setup'
                sh '''
                echo "liquid_domain: liquid.jenkins-build.example.org" > ./shared/setup/ansible/vars/config.yml
                echo "devel: true" >> ./shared/setup/ansible/vars/config.yml
                '''
                sh './buildbot run shared/setup/bin/build_image cloud'
            }
        }
    }
}
