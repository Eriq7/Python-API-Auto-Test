pipeline {
  agent any

  options {
    timestamps()
  }

  environment {
    // 避免 workspace 名字奇怪导致 compose project 名异常
    COMPOSE_PROJECT_NAME = "apitestci-${env.BUILD_NUMBER}"
    DOCKER_BUILDKIT = "1"
    COMPOSE_DOCKER_CLI_BUILD = "1"
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Docker Sanity Check') {
      steps {
        sh '''
          set -euxo pipefail
          docker version
          docker compose version
        '''
      }
    }

    stage('Patch URLs for Docker Network') {
      steps {
        sh '''
          set -euxo pipefail

          # 在 python 容器里做替换，避免 Jenkins 节点没有 python
          docker run --rm -v "$PWD":/w -w /w python:3.12-slim python - <<'PY'
import pathlib, re

root = pathlib.Path(".")
exts = {".py",".yaml",".yml",".json",".ini",".cfg",".txt",".env"}
skip_dirs = {".git",".venv","venv","__pycache__","node_modules","dist","build"}

# 1) URL 里的 host：http://localhost:xxxx / http://127.0.0.1:xxxx
# 2) 纯 host：localhost / 127.0.0.1
patterns = [
    (re.compile(r"(?<=://)(localhost|127\\.0\\.0\\.1)(?=[:/]|$)"), "target-api"),
    (re.compile(r"\\b(localhost|127\\.0\\.0\\.1)\\b"), "target-api"),
]

changed = []
for p in root.rglob("*"):
    if any(part in skip_dirs for part in p.parts):
        continue
    if not p.is_file():
        continue
    if p.suffix not in exts:
        continue
    try:
        s = p.read_text(encoding="utf-8")
    except Exception:
        continue

    t = s
    for pat, repl in patterns:
        t = pat.sub(repl, t)

    if t != s:
        p.write_text(t, encoding="utf-8")
        changed.append(str(p))

print(f"patched_files={len(changed)}")
for f in changed[:50]:
    print(" -", f)
if len(changed) > 50:
    print(f" ... (+{len(changed)-50} more)")
PY
        '''
      }
    }

    stage('Start Services (Compose)') {
      steps {
        sh '''
          set -euxo pipefail
          docker compose up -d --build
          docker compose ps
        '''
      }
    }

    stage('Wait for Services Ready') {
      steps {
        sh '''
          set -euxo pipefail

          # 用 curl 容器在 compose 网络里探活，避免 Jenkins 节点没 curl
          NET="${COMPOSE_PROJECT_NAME}_default"

          for i in $(seq 1 60); do
            if docker run --rm --network "$NET" curlimages/curl:8.6.0 \
                 -fsS "http://target-api:8000/health" >/dev/null 2>&1; then
              echo "target-api ready"
              exit 0
            fi
            sleep 2
          done

          echo "target-api NOT ready after 120s"
          docker compose ps
          exit 1
        '''
      }
    }

    stage('Trigger Tests') {
      steps {
        sh '''
          set -euxo pipefail
          NET="${COMPOSE_PROJECT_NAME}_default"

          # 在 python 容器里装依赖 + 执行测试（避免 Jenkins 节点没有 python）
          docker run --rm --network "$NET" -v "$PWD":/w -w /w python:3.12-slim sh -lc '
            python -m pip install -U pip
            if [ -f requirements.txt ]; then
              pip install -r requirements.txt
            fi

            # 优先跑项目入口：run_demo.py（常见于该类 demo 项目）
            if [ -f run_demo.py ]; then
              python run_demo.py
            else
              # 兜底：unittest discover
              python -m unittest discover -s . -p "test*.py"
            fi
          '
        '''
      }
    }
  }

  post {
    always {
      sh '''
        set +e
        docker compose ps
        docker compose logs --no-color --tail=200
        docker compose down -v
      '''
      archiveArtifacts artifacts: '**/report/**, **/reports/**, **/allure-results/**, **/log/**, **/*.log', allowEmptyArchive: true
    }
  }
}
