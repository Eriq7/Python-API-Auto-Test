pipeline {
  agent any

  options { timestamps() }

  environment {
    COMPOSE_PROJECT_NAME = "apitestci-${env.BUILD_NUMBER}"
    DOCKER_BUILDKIT = "1"
    COMPOSE_DOCKER_CLI_BUILD = "1"
    BASE_URL = "http://target-api:8000"
    RESET_PATH = "/api/test/reset"
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
        sh '''
          set -euxo pipefail
          echo "=== workspace ==="
          pwd
          ls -la
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
          PROBES="/docs /openapi.json /"

          for i in $(seq 1 60); do
            for p in $PROBES; do
              if docker run --rm --network "$NET" curlimages/curl:8.6.0 \
                   -fsSL "${BASE_URL}${p}" >/dev/null 2>&1; then
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

          # 清理 workspace 里的旧产物
          rm -rf report log || true

          # 运行测试（无论成功失败都要导出 report）
          set +e
          docker compose exec -T \
            -e BASE_URL="${BASE_URL}" \
            -e RESET_PATH="${RESET_PATH}" \
            -e REPORT_DIR="/app/report" \
            trigger sh -lc '
              set -euxo pipefail
              mkdir -p /app/report
              python run_demo.py
            '
          rc=$?
          set -e

          # ✅ 关键修复：把容器里的 /app/report 目录拷到 workspace 根目录（避免 report/report 套娃）
          docker compose cp trigger:/app/report . || true

          # 可选：如果容器里确实有 /app/log 才拷，避免无意义报错
          docker compose exec -T trigger sh -lc 'test -d /app/log' && \
            docker compose cp trigger:/app/log . || true

          echo "=== copied artifacts ==="
          find report -maxdepth 3 -type f -print || true
          find log -maxdepth 3 -type f -print || true

          exit $rc
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
      archiveArtifacts artifacts: 'report/**, log/**, **/allure-results/**, **/*.log', allowEmptyArchive: true
    }
  }
}
