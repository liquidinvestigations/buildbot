// vim: ft=groovy
properties([
    buildDiscarder(logRotator(artifactDaysToKeepStr: '', artifactNumToKeepStr: '3', daysToKeepStr: '', numToKeepStr: '3')),
    pipelineTriggers([[$class: 'PeriodicFolderTrigger', interval: '2d']])
])

parallel(
    cloud: {
        node('cloud') {
            deleteDir()
            checkout scm
            try {
                stage('X86_64: Build a Factory') {
                    sh './factory prepare-cloud-image'
                }
                parallel(
                    test: {
                        stage('X86_64: Test the image') {
                            sh './factory run true'
                        }
                    },
                    save: {
                        stage('X86_64: Save the image') {
                            sh 'cd images/cloud-x86_64 && tar c * > ../../cloud-x86_64-image.tar'
                            sh 'xz -0 < cloud-x86_64-image.tar > cloud-x86_64-image.tar.xz'
                            archiveArtifacts 'cloud-x86_64-image.tar'
                            archiveArtifacts 'cloud-x86_64-image.tar.xz'
                        }
                    }
                )
            } finally {
                deleteDir()
            }
        }
    },
    odroid_c2: {
        node('arm64') {
            deleteDir()
            checkout scm
            try {
                stage('ARM64: Build a Factory') {
                    sh './factory prepare-cloud-image'
                }
                parallel(
                    test: {
                        stage('ARM64: Test the image') {
                            sh './factory run true'
                        }
                    },
                    save: {
                        stage('ARM64: Save the image') {
                            sh 'cd images/cloud-arm64 && tar c * > ../../cloud-arm64-image.tar'
                            sh 'xz -0 < cloud-arm64-image.tar > cloud-arm64-image.tar.xz'
                            archiveArtifacts 'cloud-arm64-image.tar'
                            archiveArtifacts 'cloud-arm64-image.tar.xz'
                        }
                    }
                )
            } finally {
                deleteDir()
            }
        }
    },
    failFast: true
)
