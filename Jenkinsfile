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

          # 等 trigger 的 FastAPI 起起来（用 /docs 判活，避免纯 sleep 不稳）
          for i in $(seq 1 30); do
            if docker compose exec -T trigger python - <<'PY'
import sys, requests
try:
    r = requests.get("http://127.0.0.1:8000/docs", timeout=2)
    sys.exit(0 if r.status_code == 200 else 1)
except Exception:
    sys.exit(1)
PY
            then
              echo "trigger is up"
              break
            fi
            sleep 1
          done

          docker compose ps
        '''
      }
    }

    stage('Trigger Tests (inside trigger container)') {
      steps {
        sh '''
          set -eux

          # 在 trigger 容器里用 python+requests 调 /run-tests（不依赖 curl）
          docker compose exec -T trigger python - <<'PY'
import json, sys, requests

url = "http://127.0.0.1:8000/run-tests"
try:
    r = requests.post(url, timeout=600)
    text = r.text
except Exception as e:
    print("POST /run-tests failed:", e)
    sys.exit(2)

print(text)

try:
    data = r.json()
except Exception:
    data = {"exit_code": 1, "raw": text}

# 固定写到 /app，方便 docker compose cp
with open("/app/trigger_result.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

sys.exit(int(data.get("exit_code", 1)))
PY

          # 把产物拷回 Jenkins workspace 以便归档
          rm -rf report trigger_result.json || true
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
        # 失败时也保留关键日志，排错有用
        docker compose logs --no-color --tail=200 || true
        docker compose down -v || true
      '''
      archiveArtifacts artifacts: 'report/**/*.html,trigger_result.json', allowEmptyArchive: true
    }
  }
}
