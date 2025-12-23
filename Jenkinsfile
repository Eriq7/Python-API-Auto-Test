pipeline {
  agent any

  options {
    skipDefaultCheckout(true)
    timestamps()
  }

  environment {
    // 避免并发/残留冲突（同一台机器跑多个 job 时更稳）
    COMPOSE_PROJECT_NAME = "apitest-ci-${BUILD_NUMBER}"
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Patch URLs for Docker Network') {
      steps {
        sh '''
          set -eux

          python - <<'PY'
import pathlib

# 在 Jenkins 容器里跑 compose：应该用服务名访问 target-api
REPLACEMENTS = {
  "http://127.0.0.1:8000": "http://target-api:8000",
  "http://localhost:8000": "http://target-api:8000",
  "127.0.0.1:8000": "target-api:8000",
  "localhost:8000": "target-api:8000",
}

# 只在常见位置做 patch（不存在就跳过）
CANDIDATES = [
  "run_demo.py",
  "api_trigger.py",
  "config/setting.py",
  "config/setting.pyc",
  "lib/sendrequests.py",
]

for fp in CANDIDATES:
  p = pathlib.Path(fp)
  if not p.exists() or not p.is_file():
    continue
  try:
    txt = p.read_text(encoding="utf-8", errors="ignore")
  except Exception:
    continue

  new_txt = txt
  for old, new in REPLACEMENTS.items():
    new_txt = new_txt.replace(old, new)

  if new_txt != txt:
    p.write_text(new_txt, encoding="utf-8")
    print(f"[PATCH] {fp} updated")
PY
        '''
      }
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
          docker compose ps
        '''
      }
    }

    stage('Wait for Services Ready') {
      steps {
        sh '''
          set -eux
          # 等 target-api ready（用容器内 curl 更稳，不依赖宿主端口）
          for i in $(seq 1 30); do
            if docker compose exec -T trigger sh -lc "curl -fsS http://target-api:8000/docs >/dev/null"; then
              echo "target-api is up"
              break
            fi
            sleep 1
          done

          # 等 trigger ready
          for i in $(seq 1 30); do
            if docker compose exec -T trigger sh -lc "curl -fsS http://127.0.0.1:8000/docs >/dev/null"; then
              echo "trigger is up"
              break
            fi
            sleep 1
          done
        '''
      }
    }

    stage('Trigger Tests') {
      steps {
        sh '''
          set -eux

          # 在 trigger 容器里触发它自己的 /run-tests
          docker compose exec -T trigger sh -lc '
            curl -s -X POST http://127.0.0.1:8000/run-tests > /app/trigger_result.json
            cat /app/trigger_result.json

            python - << "PY"
import json, sys
with open("/app/trigger_result.json","r",encoding="utf-8") as f:
    data=json.load(f)
code=int(data.get("exit_code",1))
print("exit_code =", code)
sys.exit(code)
PY
          '

          # 拷贝产物回 workspace
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
        docker compose logs --no-color --tail=200 || true
        docker compose down -v || true
      '''
      archiveArtifacts artifacts: 'report/*.html,trigger_result.json', allowEmptyArchive: true
    }
  }
}
