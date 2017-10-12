// vim: ft=groovy
parallel(
    cloud: {
        node('cloud') {
            deleteDir()
            checkout scm
            stage('CLOUD: Build a Factory') {
                sh './factory prepare-cloud-image'
            }
            parallel(
                test: {
                    stage('CLOUD: Test the image') {
                        sh './factory run true'
                    }
                },
                save: {
                    stage('CLOUD: Save the image') {
                        sh 'cd images/cloud-x86_64 && tar c * > ../../cloud-x86_64-image.tar'
                        sh 'xz -0 < cloud-x86_64-image.tar > cloud-x86_64-image.tar.xz'
                        archiveArtifacts 'cloud-x86_64-image.tar'
                        archiveArtifacts 'cloud-x86_64-image.tar.xz'
                    }
                }
            )
        }
    },
    odroid_c2: {
        node('arm64') {
            deleteDir()
            checkout scm
            stage('ODROID C2: Build a Factory') {
                sh './factory prepare-cloud-image'
            }
            parallel(
                test: {
                    stage('ODROID C2: Test the image') {
                        sh './factory run true'
                    }
                },
                save: {
                    stage('ODROID C2: Save the image') {
                        sh 'cd images/cloud-arm64 && tar c * > ../../cloud-arm64-image.tar'
                        sh 'xz -0 < cloud-arm64-image.tar > cloud-arm64-image.tar.xz'
                        archiveArtifacts 'cloud-arm64-image.tar'
                        archiveArtifacts 'cloud-arm64-image.tar.xz'
                    }
                }
            )
        }
    },
    failFast: true
)
