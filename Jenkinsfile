pipeline {
    agent { label 'worker' }
    options {
        timeout(time: 30, unit: 'MINUTES')
    }

    environment {
        REPO_NAME = sh(returnStdout: true, script: 'basename `git remote get-url origin` .git').trim()
        VERSION = sh(returnStdout: true, script: 'uv version --short').trim()
        LATEST_AUTHOR = sh(returnStdout: true, script: 'git show -s --pretty=%an').trim()
        LATEST_COMMIT_ID = sh(returnStdout: true, script: 'git describe --tags --long  --always').trim()

        PYTEST_TEST_OPTIONS = ' '
        SNAPSHOT_BRANCH_REGEX = /(^main$)/
        RELEASE_REGEX = /^([0-9]+(\.[0-9]+)*)(-(RC|beta-|alpha-)[0-9]+)?$/
        RELEASE_DEPLOY = false
        SNAPSHOT_DEPLOY = false
    }

    stages {
        stage('Build Backend') {
            steps {
                script {
                    echo REPO_NAME
                    echo LATEST_AUTHOR
                    echo LATEST_COMMIT_ID

                    echo env.BRANCH_NAME
                    echo env.BUILD_NUMBER
                    echo env.TAG_NAME

                    if (!(VERSION ==~ RELEASE_REGEX || VERSION ==~ /.*-SNAPSHOT$/)) {
                        echo 'Version:'
                        echo VERSION
                        error 'The version declaration is invalid. It is neither a release nor a snapshot.'
                    }
                }
                script {
                    sh 'uv sync --locked --only-group gdal-build-dependencies'
                    sh 'uv sync --locked'
                    sh 'uv run pybabel compile -d sketch_map_tool/translations'
                    sh 'wget --quiet -P weights https://downloads.ohsome.org/sketch-map-tool/weights/SMT-OSM.pt'
                    sh 'wget --quiet -P weights https://downloads.ohsome.org/sketch-map-tool/weights/SMT-ESRI.pt'
                    sh 'wget --quiet -P weights https://downloads.ohsome.org/sketch-map-tool/weights/SMT-CLS.pt'
                    sh 'wget --quiet -P weights https://downloads.ohsome.org/sketch-map-tool/weights/SMT-SAM.pt'
                }
            }
            post {
                failure {
                  rocket_buildfail()
                }
            }
        }

        stage('Build Frontend') {
            steps {
                nodejs(nodeJSInstallationName: 'NodeJS 24') {
                    sh 'npm install'
                    sh 'npm run build'
                }
            }
            post {
                failure {
                  rocket_buildfail()
                }
            }
        }

        stage('Test') {
            environment {
                VIRTUAL_ENV="${WORKSPACE}/.venv"
                PATH="${VIRTUAL_ENV}/bin:${PATH}"
            }
            steps {
                script {
                    // run pytest
                    sh 'VCR_RECORD_MODE=none pytest --maxfail=1 --cov=sketch_map_tool --cov-report=xml tests'
                    // run static analysis with sonar-scanner
                    def scannerHome = tool 'SonarScanner 4'
                    withSonarQubeEnv('sonarcloud GIScience/ohsome') {
                        SONAR_CLI_PARAMETER =
                            "-Dsonar.python.coverage.reportPaths=${WORKSPACE}/coverage.xml " +
                            "-Dsonar.projectVersion=${VERSION}"
                        if (env.CHANGE_ID) {
                            SONAR_CLI_PARAMETER += ' ' +
                                "-Dsonar.pullrequest.key=${env.CHANGE_ID} " +
                                "-Dsonar.pullrequest.branch=${env.CHANGE_BRANCH} " +
                                "-Dsonar.pullrequest.base=${env.CHANGE_TARGET}"
                        } else {
                            SONAR_CLI_PARAMETER += ' ' +
                                "-Dsonar.branch.name=${env.BRANCH_NAME}"
                        }
                        sh "${scannerHome}/bin/sonar-scanner " + SONAR_CLI_PARAMETER
                    }
                    // run other static code analysis and checks
                    sh 'pre-commit run --all-files'
                }
            }
            post {
                failure {
                  rocket_testfail()
                }
            }
        }

        stage('Wrapping Up') {
            steps {
                encourage()
                status_change()
            }
        }
    }
}
