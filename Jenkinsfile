// vim: ft=groovy
properties([
    buildDiscarder(logRotator(artifactDaysToKeepStr: '', artifactNumToKeepStr: '3', daysToKeepStr: '', numToKeepStr: '3')),
    pipelineTriggers([[$class: 'PeriodicFolderTrigger', interval: '2d']])
])

parallel(

  x86_64_test: {
    node('cloud') {
      deleteDir()
      checkout scm
      try {
        stage('X86_64: Run the test suite') {
          sh 'virtualenv -p python3 venv'
          sh './venv/bin/python ./venv/bin/pip install -r requirements.txt'
          sh './venv/bin/python ./venv/bin/pytest'
        }
      } finally {
        deleteDir()
      }
    }
  },

  x86_64_build: {
    node('cloud') {
      deleteDir()
      checkout scm
      try {
        stage('X86_64: Build a reusable image') {
          sh './factory prepare-cloud-image'
        }
        stage('X86_64: Check the image') {
          sh './factory run true'
        }
        stage('X86_64: Save artifacts') {
          sh 'cd images/cloud-x86_64 && tar c * > ../../cloud-x86_64-image.tar'
          sh 'xz -0 < cloud-x86_64-image.tar > cloud-x86_64-image.tar.xz'
          archiveArtifacts 'cloud-x86_64-image.tar'
          archiveArtifacts 'cloud-x86_64-image.tar.xz'
        }
      } finally {
        deleteDir()
      }
    }
  }

  arm64_test: {
    node('arm64') {
      deleteDir()
      checkout scm
      try {
        stage('ARM64: Run the test suite') {
          sh 'virtualenv -p python3 venv'
          sh './venv/bin/python ./venv/bin/pip install -r requirements.txt'
          sh './venv/bin/python ./venv/bin/pytest'
        }
      } finally {
          deleteDir()
      }
    }
  },

  arm64_build: {
    node('arm64') {
      deleteDir()
      checkout scm
      try {
        stage('ARM64: Build a reusable image') {
          sh './factory prepare-cloud-image'
        }
        stage('ARM64: Check the image') {
          sh './factory run true'
        }
        stage('ARM64: Save artifacts') {
          sh 'cd images/cloud-arm64 && tar c * > ../../cloud-arm64-image.tar'
          sh 'xz -0 < cloud-arm64-image.tar > cloud-arm64-image.tar.xz'
          archiveArtifacts 'cloud-arm64-image.tar'
          archiveArtifacts 'cloud-arm64-image.tar.xz'
        }
      } finally {
          deleteDir()
      }
    }
  }

  failFast: true
)
