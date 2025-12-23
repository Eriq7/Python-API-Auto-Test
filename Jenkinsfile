pipeline {
  agent any

  stages {
    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Docker Sanity Check') {
      steps {
        sh '''
          set -eux
          docker version
          docker compose version
        '''
      }
    }

    stage('Start Services (Compose)') {
      steps {
        sh '''
          set -eux
          docker compose up -d --build
          sleep 2
          docker compose ps
        '''
      }
    }

    stage('Trigger Tests (inside trigger container)') {
      steps {
        sh '''
          set -eux

          # 在 trigger 容器内部调用 trigger 自己的接口（容器内监听 8000）
          docker compose exec -T trigger sh -lc '
            curl -s -X POST http://127.0.0.1:8000/run-tests > trigger_result.json
            cat trigger_result.json

            python - << "PY"
import json, sys
with open("trigger_result.json","r",encoding="utf-8") as f:
    data=json.load(f)
code=int(data.get("exit_code",1))
print("exit_code =", code)
sys.exit(code)
PY
          '

          # 把产物拷回 Jenkins workspace（方便归档）
          rm -rf report || true
          rm -f trigger_result.json || true
          docker compose cp trigger:/app/trigger_result.json ./trigger_result.json || true
          docker compose cp trigger:/app/report ./report || true
        '''
      }
    }
  }

  post {
    always {
      sh '''
        set +e
        docker compose down -v || true
      '''
      archiveArtifacts artifacts: 'report/*.html,trigger_result.json', allowEmptyArchive: true
    }
  }
}
