## Running Sonarqube locally with Docker


- see https://docs.sonarqube.org/9.6/try-out-sonarqube/

#### Start the Sonarqube server with Docker

```bash
docker run -d --name sonarqube -e SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true -p 9000:9000 sonarqube:latest

```

- Then login to http://localhost:9000 with admin/admin, will be prompted to change password.
- Create a new project, e.g. "my-project", will need these details in the next step


#### Analyze a project

```bash

# Get the below from the Sonarqube UI

SONARQUBE_URL="http://127.0.0.1:9000"
YOUR_PROJECT_KEY="xx"
AUTH_TOKEN="sqp_xxxxxxxxxxxxxxxxxxxxxxxx"
YOUR_REPO='absolute/path/to/your/repo'



docker run \
    --rm \
    --network=host \
    -e SONAR_HOST_URL="${SONARQUBE_URL}" \
    -e SONAR_SCANNER_OPTS="-Dsonar.projectKey=${YOUR_PROJECT_KEY}" \
    -e SONAR_LOGIN="${AUTH_TOKEN}" \
    -v "${YOUR_REPO}:/usr/src" \
    sonarsource/sonar-scanner-cli

```

- Then go back to the UI and see the results.
