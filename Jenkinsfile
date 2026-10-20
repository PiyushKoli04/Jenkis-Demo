pipeline {
    agent any

    environment {
        DOCKERHUB_USER = 'piyushkoli04'
        IMAGE = "${DOCKERHUB_USER}/expense-tracker"
    }

    triggers {
        githubPush()
        pollSCM('H/5 * * * *')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    python3 -m venv venv
                    venv/bin/pip install --upgrade pip
                    venv/bin/pip install -r requirements.txt
                '''
            }
        }

        stage('Build') {
            steps {
                sh '''
                    venv/bin/python -m py_compile app.py
                '''
            }
        }

        stage('Test') {
            steps {
                sh '''
                    venv/bin/pytest -v --junitxml=report.xml
                '''
            }
            post {
                always {
                    junit 'report.xml'
                }
            }
        }

        stage('Docker Build') {
            steps {
                sh """
                    docker build -t ${IMAGE}:${BUILD_NUMBER} -t ${IMAGE}:latest .
                """
            }
        }

        stage('Docker Push') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh """
                        echo "\$DOCKER_PASS" | docker login -u "\$DOCKER_USER" --password-stdin
                        docker push ${IMAGE}:${BUILD_NUMBER}
                        docker push ${IMAGE}:latest
                        docker logout
                    """
                }
            }
        }

        stage('Deploy') {
            steps {
                sh """
                    docker rm -f expense-app || true
                    docker run -d --name expense-app --network devops-net -p 5000:5000 -v expense-data:/data ${IMAGE}:latest
                    sleep 5
                    curl -f http://expense-app:5000/health
                """
            }
        }
    }

    post {
        success {
            echo "Pipeline succeeded! Expense Tracker was built, tested, pushed, and deployed."
        }
        failure {
            echo "Pipeline failed! Please check console output and test reports."
        }
    }
}
