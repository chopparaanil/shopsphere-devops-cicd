
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

        stage('SonarQube Analysis') {
            steps {
                script {
                    def scannerHome = tool 'SonarScanner'

                    withSonarQubeEnv('SonarQube') {
                        sh """
                            ${scannerHome}/bin/sonar-scanner \
                              -Dsonar.projectKey=ShopSphere \
                              -Dsonar.projectName=ShopSphere \
                              -Dsonar.sources=app \
                              -Dsonar.tests=tests \
                              -Dsonar.python.version=3.12 \
                              -Dsonar.exclusions=**/.venv-ci/**,**/__pycache__/** \
                              -Dsonar.sourceEncoding=UTF-8
                        """
                    }
                }
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
                    NETWORK="shopsphere-ci-${BUILD_NUMBER}"
                    CONTAINER="shopsphere-ci-test-${BUILD_NUMBER}"

                    cleanup() {
                        docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
                        docker network rm "$NETWORK" >/dev/null 2>&1 || true
                    }

                    trap cleanup EXIT

                    echo "Creating temporary Docker network..."
                    docker network create "$NETWORK"

                    echo "Starting ShopSphere container..."
                    docker run -d \
                        --name "$CONTAINER" \
                        --network "$NETWORK" \
                        "$IMAGE"

                    echo "Checking ShopSphere health endpoint..."

                    ATTEMPT=0
                    until docker run --rm \
                        --network "$NETWORK" \
                        curlimages/curl:8.12.1 \
                        --fail --silent --show-error \
                        "http://${CONTAINER}:7000/health"; do

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

                    docker run --rm \
                        --network "$NETWORK" \
                        curlimages/curl:8.12.1 \
                        --fail --silent --show-error \
                        "http://${CONTAINER}:7000/ready"

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
