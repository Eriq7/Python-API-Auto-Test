pipeline {
  agent any

  stages {
    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Start Services (Compose)') {
      steps {
        sh 'docker compose up -d --build'
        sh 'sleep 2'
      }
    }

    stage('Trigger Tests') {
      steps {
        sh '''
          curl -s -X POST http://127.0.0.1:9000/run-tests > trigger_result.json
          cat trigger_result.json

          python - << 'PY'
import json, sys
with open("trigger_result.json","r",encoding="utf-8") as f:
    data=json.load(f)
code=int(data.get("exit_code",1))
print("exit_code =", code)
sys.exit(code)
PY
        '''
      }
    }
  }

  post {
    always {
      sh 'docker compose down -v || true'
      archiveArtifacts artifacts: 'report/*.html,trigger_result.json', allowEmptyArchive: true
    }
  }
}
