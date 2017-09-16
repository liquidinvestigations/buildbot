pipeline {
    agent any
    stages {
        stage('Prepare Cloud Image') {
            agent any
            steps {
                sh 'git clone https://github.com/liquidinvestigations/setup.git shared/setup'
                sh './prepare_cloud_image.py'
            }
        }
        stage('Write Configuration') {
            agent any
            steps {
                sh '''
                echo "liquid_domain: liquid.jenkins-build.example.org" > ./shared/setup/ansible/vars/config.yml
                echo "devel: true" >> ./shared/setup/ansible/vars/config.yml
                '''
            }
        }
        stage('Build Cloud Image') {
            agent {
                label 'cloud'
            }
            steps {
                sh './buildbot run shared/setup/bin/build_image cloud'
            }
            post {
                always {
                    archive 'shared/ubuntu-x86_64-raw.img'
                }
            }
        }

        stage('Convert Cloud Images') {
            agent {
                label 'cloud'
            }
            steps {
                sh 'qemu-img convert -f raw -O qcow2 shared/ubuntu-x86_64-raw.img shared/ubuntu-x86_64-cow2.img'
            }
            post {
                always {
                    archive 'shared/ubuntu-x86_64-cow2.img'
                }
            }
        }

        stage('Build Odroid C2 Image') {
            agent {
                label 'odroid_c2'
            }
            steps {
                sh './buildbot run shared/setup/bin/build_image odroid_c2'
            }
            post {
                always {
                    archive 'shared/ubuntu-odroid_c2-raw.img'
                }
            }
        }
    }
}
