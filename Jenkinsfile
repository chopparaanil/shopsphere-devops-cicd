
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

        
     
        stage('Push Image to Amazon ECR') {
            steps {
                withCredentials([[
                    $class: 'AmazonWebServicesCredentialsBinding',
                    credentialsId: 'aws-ecr-credentials'
                ]]) {
                    sh '''
                        set -eu

                        AWS_REGION="ap-south-1"
                        AWS_ACCOUNT_ID="597787442390"
                        ECR_REPOSITORY="shopsphere"
                        ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
                        LOCAL_IMAGE="shopsphere-app:${BUILD_NUMBER}"
                        ECR_IMAGE="${ECR_REGISTRY}/${ECR_REPOSITORY}:${BUILD_NUMBER}"

                        echo "Checking AWS identity..."
                        /usr/local/bin/aws sts get-caller-identity \
                            --region "$AWS_REGION" \
                            --query Account \
                            --output text

                        echo "Authenticating with Amazon ECR..."
                        /usr/local/bin/aws ecr get-login-password \
                            --region "$AWS_REGION" |
                            /usr/bin/docker login \
                                --username AWS \
                                --password-stdin "$ECR_REGISTRY"

                        echo "Tagging image..."
                        /usr/bin/docker tag "$LOCAL_IMAGE" "$ECR_IMAGE"

                        echo "Pushing image to Amazon ECR..."
                        /usr/bin/docker push "$ECR_IMAGE"

                        echo "Successfully pushed: $ECR_IMAGE"
                    '''
                }
            }
        }
        stage('Update Kubernetes Manifest') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'github-credentials',
                        usernameVariable: 'GIT_USERNAME',
                        passwordVariable: 'GIT_TOKEN'
                    )
                ]) {
                    sh '''
                        set -eu
                        set +x

                        ECR_IMAGE="597787442390.dkr.ecr.ap-south-1.amazonaws.com/shopsphere:${BUILD_NUMBER}"

                        echo "Updating Kubernetes deployment manifest..."

                        sed -i "s|image: 597787442390.dkr.ecr.ap-south-1.amazonaws.com/shopsphere:.*|image: ${ECR_IMAGE}|" k8s/deployment.yaml

                        git config user.name "Jenkins"
                        git config user.email "jenkins@example.com"

                        git add k8s/deployment.yaml

                        if git diff --cached --quiet; then
                            echo "No manifest changes to commit."
                            exit 0
                        fi

                        git commit -m "Update ShopSphere image to ${BUILD_NUMBER} [skip ci]"

                        ASKPASS_SCRIPT="$(mktemp)"
                        trap 'rm -f "$ASKPASS_SCRIPT"' EXIT

                        cat > "$ASKPASS_SCRIPT" <<'EOF'
#!/bin/sh
case "$1" in
    *Username*) printf '%s\\n' "$GIT_USERNAME" ;;
    *Password*) printf '%s\\n' "$GIT_TOKEN" ;;
    *) exit 1 ;;
esac
EOF

                        chmod 700 "$ASKPASS_SCRIPT"

                        export GIT_ASKPASS="$ASKPASS_SCRIPT"
                        export GIT_TERMINAL_PROMPT=0

                        echo "Pushing updated manifest to GitHub..."
                        git push origin HEAD:main

                        echo "GitOps manifest pushed successfully."
                    '''
                }
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
