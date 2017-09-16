pipeline {
    agent any
    stages {
        stage('Build Cloud Image') {
            steps {
                sh 'echo "Starting configuring and x86 build..."'
                sh './prepare_cloud_image.py'
                sh 'git clone https://github.com/liquidinvestigations/setup.git shared/setup'
                sh '''
                echo "liquid_domain: liquid.jenkins-build.example.org" > ./shared/setup/ansible/vars/config.yml
                echo "devel: true" >> ./shared/setup/ansible/vars/config.yml
                '''
                sh './buildbot run shared/setup/bin/build_image cloud'
                sh 'qemu-img convert -f raw -O qcow2 shared/ubuntu-x86_64-raw.img shared/ubuntu-x86_64-cow2.img'
            }
        }
    }

    post {
        always {
            archive 'shared/ubuntu-x86_64-raw.img'
            archive 'shared/ubuntu-x86_64-cow2.img'
        }
    }
}
