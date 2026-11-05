pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {
        stage('Verificar') {
            steps {
                sh '''
                    python3 -m venv .venv-ci
                    .venv-ci/bin/python -m pip install -q -r requirements.txt
                    .venv-ci/bin/python -m compileall -q app run.py setup_db.py
                '''
            }
        }

        stage('Instalar') {
            steps {
                // O script fica em /opt, dono do root, e só aceita este workspace.
                sh 'sudo /opt/catalogo-web/deploy-catalogo-web.sh "$WORKSPACE"'
            }
        }
    }
}
