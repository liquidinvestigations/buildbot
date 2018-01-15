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
          sh './venv/bin/python ./venv/bin/pytest --junitxml x86_64-results.xml'
        }
      }
      finally {
          if (fileExists('x86_64-results.xml')) {
            junit 'x86_64-results.xml'
          }
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
          sh './factory export cloud-x86_64 | gzip -1 > xenial-x86_64.factory.gz'
          archiveArtifacts 'xenial-x86_64.factory.gz'

          sh 'cd images/cloud-x86_64 && tar c * > ../../cloud-x86_64-image.tar'
          sh 'gzip -1 < cloud-x86_64-image.tar > cloud-x86_64-image.tar.gz'
          archiveArtifacts 'cloud-x86_64-image.tar.gz'
        }
      }
      finally {
        deleteDir()
      }
    }
  },

  x86_64_build_artful: {
    node('cloud') {
      deleteDir()
      checkout scm
      try {
        stage('X86_64: Build a reusable image') {
          sh './factory prepare-cloud-image --flavor artful'
        }
        stage('X86_64: Check the image') {
          sh './factory run true'
        }
        stage('X86_64: Save artifacts') {
          sh './factory export cloud-x86_64 | gzip -1 > artful-x86_64.factory.gz'
          archiveArtifacts 'artful-x86_64.factory.gz'
        }
      }
      finally {
        deleteDir()
      }
    }
  },

  x86_64_installer: {
    node('cloud') {
      deleteDir()
      checkout scm
      try {
        stage('X86_64: Run the installer') {
          sh "#!/bin/bash\n" +
             "python3 <(cat install.py) installertarget"
          sh './installertarget/factory run true'
        }
      }
      finally {
        deleteDir()
      }
    }
  },

  x86_64_installer_artful: {
    node('cloud') {
      deleteDir()
      checkout scm
      try {
        stage('X86_64: Run the installer') {
          sh "#!/bin/bash\n" +
             "python3 <(cat install.py) installertarget --image https://jenkins.liquiddemo.org/job/liquidinvestigations/job/factory/job/PR-32/5/artifact/artful-x86_64.factory.gz"
          sh './installertarget/factory run true'
        }
      }
      finally {
        deleteDir()
      }
    }
  },

  arm64_test: {
    node('arm64') {
      deleteDir()
      checkout scm
      try {
        stage('ARM64: Run the test suite') {
          sh 'virtualenv -p python3 venv'
          sh './venv/bin/python ./venv/bin/pip install -r requirements.txt'
          sh './venv/bin/python ./venv/bin/pytest --junitxml arm64-results.xml'
        }
      }
      finally {
          if (fileExists('arm64-results.xml')) {
            junit 'arm64-results.xml'
          }
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
          sh './factory export cloud-arm64 | gzip -1 > xenial-arm64.factory.gz'
          archiveArtifacts 'xenial-arm64.factory.gz'

          sh 'cd images/cloud-arm64 && tar c * > ../../cloud-arm64-image.tar'
          sh 'gzip -1 < cloud-arm64-image.tar > cloud-arm64-image.tar.gz'
          archiveArtifacts 'cloud-arm64-image.tar.gz'
        }
      }
      finally {
          deleteDir()
      }
    }
  },

  arm64_build_artful: {
    node('arm64') {
      deleteDir()
      checkout scm
      try {
        stage('ARM64: Build a reusable image') {
          sh './factory prepare-cloud-image --flavor artful'
        }
        stage('ARM64: Check the image') {
          sh './factory run true'
        }
        stage('ARM64: Save artifacts') {
          sh './factory export cloud-arm64 | gzip -1 > artful-arm64.factory.gz'
          archiveArtifacts 'artful-arm64.factory.gz'
        }
      }
      finally {
          deleteDir()
      }
    }
  },

  arm64_installer: {
    node('arm64') {
      deleteDir()
      checkout scm
      try {
        stage('ARM64: Run the installer') {
          sh "#!/bin/bash\n" +
             "python3 <(cat install.py) installertarget"
          sh './installertarget/factory run true'
        }
      }
      finally {
        deleteDir()
      }
    }
  },

  arm64_installer_artful: {
    node('arm64') {
      deleteDir()
      checkout scm
      try {
        stage('ARM64: Run the installer') {
          sh "#!/bin/bash\n" +
             "python3 <(cat install.py) installertarget --image https://jenkins.liquiddemo.org/job/liquidinvestigations/job/factory/job/PR-32/5/artifact/artful-arm64.factory.gz"
          sh './installertarget/factory run true'
        }
      }
      finally {
        deleteDir()
      }
    }
  },

  failFast: false
)
