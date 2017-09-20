// vim: ft=groovy
parallel(
    cloud: {
        node('cloud') {
            deleteDir()
            checkout scm
            stage('CLOUD: Setup the setup repo') {
                sh './setup_setup'
            }
            stage('CLOUD: Prepare Cloud Image') {
                sh './prepare_cloud_image.py'
            }
            stage('CLOUD: Build Image') {
                sh './buildbot run shared/setup/bin/build_image cloud'
            }
            stage("CLOUD: Run first boot") {
                sh 'cp shared/ubuntu-x86_64-raw.img images/liquid-cloud-x86_64/disk.img'
                sh './buildbot --platform liquid-cloud-x86_64 run shared/setup/bin/wait_first_boot.py'
            }
            stage('CLOUD: Archive Raw Image') {
                // The archiveArtifacts command keeps the relative path of the
                // file as the filename. To avoid this issue, we move all
                // binaries that will be archived to the workspace root.
                sh 'xz -1 < shared/ubuntu-x86_64-raw.img > liquid-cloud-x86_64-raw.img.xz'
                archiveArtifacts 'liquid-cloud-x86_64-raw.img.xz'
            }
            stage('CLOUD: Create Vagrant box for VirtualBox provider') {
                sh './buildbot run shared/setup/bin/convert-image.sh'
                sh 'mv shared/output/ubuntu-x86_64-vbox.box liquid-cloud-x86_64-vbox.box'
                archiveArtifacts 'liquid-cloud-x86_64-vbox.box'
            }
        }
    },
    odroid_c2: {
        node('odroid_c2') {
            deleteDir()
            checkout scm
            stage('ODROID C2: Setup the setup repo') {
                sh './setup_setup'
            }
            stage('ODROID C2: Prepare Cloud Image') {
                sh './prepare_cloud_image.py'
            }
            stage('ODROID C2: Build Image') {
                sh './buildbot run shared/setup/bin/build_image odroid_c2'
            }
            stage('ODROID C2: Archive Raw Image') {
                sh 'xz -1 < shared/ubuntu-odroid_c2-raw.img > liquid-odroid_c2-arm64-raw.img.xz'
                archiveArtifacts 'liquid-odroid_c2-arm64-raw.img.xz'
            }
        }
    },
    failFast: true
)
