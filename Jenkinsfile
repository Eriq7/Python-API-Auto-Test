pipeline {
  agent any

  options { timestamps() }

  environment {
    COMPOSE_PROJECT_NAME = "apitestci-${env.BUILD_NUMBER}"
    DOCKER_BUILDKIT = "1"
    COMPOSE_DOCKER_CLI_BUILD = "1"
    // 统一把测试指向 compose 里的 target-api
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

          # 先清理 workspace 里的旧产物
          rm -rf report log || true
          mkdir -p report log

          # 运行测试：无论成功失败，都要把 /app/report 拷出来
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

          # 把容器里生成的报告/日志拷回 Jenkins workspace（否则 archiveArtifacts 抓不到）
          docker compose cp trigger:/app/report ./report || true
          docker compose cp trigger:/app/log ./log || true

          echo "=== copied artifacts ==="
          find report -maxdepth 2 -type f -print || true
          find log -maxdepth 2 -type f -print || true

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
