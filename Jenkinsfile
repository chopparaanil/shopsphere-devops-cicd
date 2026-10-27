
pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Verify Build Environment') {
            steps {
                sh '''
                    echo "Checking Jenkins environment..."
                    java -version
                    git --version
                    docker --version
                '''
            }
        }

        stage('Build and Test') {
            steps {
                script {
                    docker.image('python:3.12-slim').inside('-u root') {
                        sh '''
                            python --version
                            python -m venv .venv-ci
                            .venv-ci/bin/python -m pip install --upgrade pip
                            .venv-ci/bin/python -m pip install -r requirements.txt
                            .venv-ci/bin/python -m pytest -v --junitxml=pytest-results.xml
                        '''
                    }
                }
            }

            post {
                always {
                    junit testResults: 'pytest-results.xml',
                          allowEmptyResults: true
                }
            }
        }

        stage('Application Validation') {
            steps {
                script {
                    docker.image('python:3.12-slim').inside('-u root') {
                        sh '''
                            python -m compileall -q app tests
                            echo "Application validation completed."
                        '''
                    }
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    def imageTag = "shopsphere-app:${env.BUILD_NUMBER}"
                    docker.build(imageTag)
                }
            }
        }

        stage('Docker Health Check') {
            steps {
                sh '''
                    set -eu

                    IMAGE="shopsphere-app:${BUILD_NUMBER}"
                    CONTAINER="shopsphere-ci-test-${BUILD_NUMBER}"

                    cleanup() {
                        docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
                    }

                    trap cleanup EXIT

                    echo "Starting ShopSphere container..."
                    docker run -d \
                        --name "$CONTAINER" \
                        -p 127.0.0.1::7000 \
                        "$IMAGE"

                    PORT=$(docker port "$CONTAINER" 7000/tcp | sed 's/.*://')

                    echo "Checking ShopSphere health endpoint..."

                    ATTEMPT=0
                    until curl --fail --silent "http://127.0.0.1:${PORT}/health"; do
                        ATTEMPT=$((ATTEMPT + 1))

                        if [ "$ATTEMPT" -ge 15 ]; then
                            echo "Health check failed."
                            docker logs "$CONTAINER"
                            exit 1
                        fi

                        sleep 2
                    done

                    echo ""
                    echo "Checking ShopSphere readiness endpoint..."
                    curl --fail --silent "http://127.0.0.1:${PORT}/ready"
                    echo ""

                    echo "Docker image health checks passed."
                '''
            }
        }
    }

    post {
        success {
            echo 'ShopSphere CI pipeline completed successfully.'
        }

        failure {
            echo 'ShopSphere CI pipeline failed. Check the stage logs.'
        }

        always {
            echo 'ShopSphere pipeline execution finished.'
        }
    }
}
