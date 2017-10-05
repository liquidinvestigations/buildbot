// vim: ft=groovy
parallel(
    cloud: {
        node('cloud') {
            deleteDir()
            checkout scm
            stage('CLOUD: Build a Factory') {
                sh './factory prepare-cloud-image'
                sh 'cd images/cloud-x86_64 && tar c * | xz > ../../cloud-x86_64-image.tar.xz'
                archiveArtifacts 'cloud-x86_64-image.tar.xz'
            }
        }
    },
    odroid_c2: {
        node('arm64') {
            deleteDir()
            checkout scm
            stage('ODROID C2: Build a Factory') {
                sh './factory prepare-cloud-image'
                sh 'cd images/cloud-arm64 && tar c * | xz -0 > ../../cloud-arm64-image.tar.xz'
                archiveArtifacts 'cloud-arm64-image.tar.xz'
            }
        }
    },
    failFast: true
)
