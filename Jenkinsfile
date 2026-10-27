
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
                '''
            }
        }

        stage('Build and Test') {
            steps {
                sh '''
                    echo "Checking Python image availability..."
                    echo "Python tests will run in a separate container."
                '''

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
