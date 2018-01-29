pipeline {
  agent any
  stages {
    stage('Build') {
      parallel {
        stage('son-gtkapi') {
          steps {
            dir(path: 'tests/integration/build') {
              sh './gtkapi.sh'
            }
            
          }
        }
        stage('son-gtkfnct') {
          steps {
            dir(path: 'tests/integration/build') {
              sh './gtkfnct.sh'
            }
            
          }
        }
        stage('son-keycloak') {
          steps {
            dir(path: 'tests/integration/build') {
              sh './gtkkeycloak.sh'
            }
            
          }
        }
        stage('son-gtkkpi') {
          steps {
            dir(path: 'tests/integration/build') {
              sh './gtkkpi.sh'
            }
            
          }
        }
        stage('son-gtklic') {
          steps {
            dir(path: 'tests/integration/build') {
              sh './gtklic.sh'
            }
            
          }
        }
        stage('son-gtkpkg') {
          steps {
            dir(path: 'tests/integration/build') {
              sh './gtkpkg.sh'
            }
            
          }
        }
        stage('son-gtkrec') {
          steps {
            dir(path: 'tests/integration/build') {
              sh './gtkrec.sh'
            }
            
          }
        }
        stage('son-gtkrlt') {
          steps {
            dir(path: 'tests/integration/build') {
              sh './gtkrlt.sh'
            }
            
          }
        }
        stage(' son-gtksrv') {
          steps {
            dir(path: 'tests/integration/build') {
              sh './gtksrv.sh'
            }
            
          }
        }
        stage('son-gtkusr') {
          steps {
            dir(path: 'tests/integration/build') {
              sh './gtkusr.sh'
            }
            
          }
        }
        stage('son-gtkvim') {
          steps {
            dir(path: 'tests/integration/build') {
              sh './gtkvim.sh'
            }
            
          }
        }
        stage('son-sec-gw') {
          steps {
            dir(path: 'tests/integration/build') {
              sh './son-sec-gw.sh'
            }
            
          }
        }
      }
    }
    stage('Checkstyle') {
      steps {
        dir(path: 'tests/checkstyle') {
          sh './gtkall.sh'
        }
        
      }
    }
    stage('Unit Tests Dependencies') {
      steps {
        dir(path: 'tests/unit') {
          sh './test-dependencies.sh'
        }
        
      }
    }
    stage('Unit Test Run') {
      parallel {
        stage('Unit Test Run') {
          steps {
            dir(path: 'tests/unit') {
              sh './gtkapi.sh'
            }
            
          }
        }
        stage('son-gtkfnct') {
          steps {
            dir(path: 'tests/unit') {
              sh './gtkfnct.sh'
            }
            
          }
        }
        stage('son-gtkkpi') {
          steps {
            dir(path: 'tests/unit') {
              sh './gtkkpi.sh'
            }
            
          }
        }
        stage('son-gtklic') {
          steps {
            dir(path: 'tests/unit') {
              sh './gtklic.sh'
            }
            
          }
        }
        stage('son-gtkpkg') {
          steps {
            dir(path: 'tests/unit') {
              sh './gtkpkg.sh'
            }
            
          }
        }
        stage('son-gtkrlt') {
          steps {
            dir(path: 'tests/unit') {
              sh './gtkrlt.sh'
            }
            
          }
        }
        stage('son-gtksrv') {
          steps {
            dir(path: 'tests/unit') {
              sh './gtksrv.sh'
            }
            
          }
        }
        stage('son-gtkvim') {
          steps {
            dir(path: 'tests/unit') {
              sh './gtkvim.sh'
            }
            
          }
        }
      }
    }
    stage('Containers Publication') {
      parallel {
        stage('son-gtkapi') {
          steps {
            sh 'docker push registry.sonata-nfv.eu:5000/son-gtkapi'
          }
        }
        stage('son-gtkfnct') {
          steps {
            sh 'docker push registry.sonata-nfv.eu:5000/son-gtkfnct'
          }
        }
        stage('son-gtkkeycloak') {
          steps {
            sh 'docker push registry.sonata-nfv.eu:5000/son-keycloak'
          }
        }
        stage('son-gtkkpi') {
          steps {
            sh 'docker push registry.sonata-nfv.eu:5000/son-gtkkpi'
          }
        }
        stage('son-gtklic') {
          steps {
            sh 'docker push registry.sonata-nfv.eu:5000/son-gtklic'
          }
        }
        stage('son-gtkpkg') {
          steps {
            sh 'docker push registry.sonata-nfv.eu:5000/son-gtkpkg'
          }
        }
        stage('son-gtkrec') {
          steps {
            sh 'docker push registry.sonata-nfv.eu:5000/son-gtkrec'
          }
        }
        stage('son-gtkrlt') {
          steps {
            sh 'docker push registry.sonata-nfv.eu:5000/son-gtkrlt'
          }
        }
        stage('son-gtksrv') {
          steps {
            sh 'docker push registry.sonata-nfv.eu:5000/son-gtksrv'
          }
        }
        stage('son-gtkusr') {
          steps {
            sh 'docker push registry.sonata-nfv.eu:5000/son-gtkusr'
          }
        }
        stage('son-gtkvim') {
          steps {
            sh 'docker push registry.sonata-nfv.eu:5000/son-gtkvim'
          }
        }
        stage('son-sec-gw') {
          steps {
            sh 'docker push registry.sonata-nfv.eu:5000/son-sec-gw'
          }
        }
      }
    }
    stage('Integration - Deployment') {
      environment {
        ENV_INT_SERVER = 'sp.int.sonata-nfv.eu'
      }
      steps {
        dir(path: 'tests/integration') {
          sh './deploy.sh'
        }
        
      }
    }
    stage('Integration - Test') {
      environment {
        ENV_INT_SERVER = 'sp.int.sonata-nfv.eu'
      }
      steps {
        dir(path: 'tests/integration') {
          sh './funtionaltests.sh localhost'
        }
        
      }
    }
    stage('Publish results') {
      steps {
        junit(allowEmptyResults: true, testResults: 'tests/unit/spec/reports/**/*.xml')
        checkstyle(pattern: 'tests/checkstyle/reports/checkstyle-*.xml')
        archive 'tests/checkstyle/reports/checkstyle-*.html'
      }
    }
  }
  post {
    success {
        emailext (
          subject: "SUCCESS: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]'",
          body: """<p>SUCCESS: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]':</p>
            <p>Check console output at &QUOT;<a href='${env.BUILD_URL}'>${env.JOB_NAME} [${env.BUILD_NUMBER}]</a>&QUOT;</p>""",
        recipientProviders: [[$class: 'DevelopersRecipientProvider']]
        )
      }
    failure {
      emailext (
          subject: "FAILED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]'",
          body: """<p>FAILED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]':</p>
            <p>Check console output at &QUOT;<a href='${env.BUILD_URL}'>${env.JOB_NAME} [${env.BUILD_NUMBER}]</a>&QUOT;</p>""",
          recipientProviders: [[$class: 'DevelopersRecipientProvider']]
        )
    }  
  }
}