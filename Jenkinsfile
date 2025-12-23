pipeline {
  agent any

  options { timestamps() }

  environment {
    COMPOSE_PROJECT_NAME = "apitestci-${env.BUILD_NUMBER}"
    DOCKER_BUILDKIT = "1"
    COMPOSE_DOCKER_CLI_BUILD = "1"
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
        sh '''
          set -euxo pipefail
          echo "=== host workspace check ==="
          pwd
          ls -la
          echo "=== top files ==="
          find . -maxdepth 2 -type f | sed -n '1,120p'
        '''
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
          docker run --rm -v "$PWD":/w -w /w python:3.12-slim python - <<'PY'
import pathlib, re

root = pathlib.Path(".")
exts = {".py",".yaml",".yml",".json",".ini",".cfg",".txt",".env"}
skip_dirs = {".git",".venv","venv","__pycache__","node_modules","dist","build"}

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
          NET="${COMPOSE_PROJECT_NAME}_default"
          PROBES="/health /docs /openapi.json /"

          for i in $(seq 1 60); do
            for p in $PROBES; do
              if docker run --rm --network "$NET" curlimages/curl:8.6.0 \
                   -fsSL "http://target-api:8000${p}" >/dev/null 2>&1; then
                echo "target-api ready via ${p}"
                exit 0
              fi
            done
            sleep 2
          done

          echo "target-api NOT ready after 120s"
          docker compose ps
          docker compose logs --no-color --tail=200 target-api || true
          exit 1
        '''
      }
    }

    stage('Trigger Tests') {
      steps {
        sh '''
          set -euxo pipefail
          NET="${COMPOSE_PROJECT_NAME}_default"

          echo "=== host workspace sanity before tests ==="
          pwd
          ls -la
          test -f requirements.txt || true
          test -f run_demo.py || true

          docker run --rm --network "$NET" -v "$PWD":/w -w /w python:3.12-slim sh -lc '
            set -euxo pipefail
            echo "=== inside container workspace check ==="
            pwd
            ls -la
            echo "=== inside container top files ==="
            find . -maxdepth 2 -type f | sed -n "1,120p"

            # 如果这里还是空目录，直接报错（别再浪费一次 build）
            cnt=$(find . -maxdepth 1 -type f | wc -l | tr -d " ")
            if [ "$cnt" -eq 0 ]; then
              echo "ERROR: workspace mounted into container is empty. Checkout/mount path is wrong."
              exit 22
            fi

            python -m pip install -U pip
            if [ -f requirements.txt ]; then
              pip install -r requirements.txt
            fi

            if [ -f run_demo.py ]; then
              python run_demo.py
              exit 0
            fi

            # 兜底：按常见目录跑
            for d in testcase testcases tests test; do
              if [ -d "$d" ]; then
                python -m unittest discover -s "$d" -p "*.py" -t .
                exit 0
              fi
            done

            python -m unittest discover -s . -p "test*.py" -t .
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
