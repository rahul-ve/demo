## MLflow Examples


### Local tracking using SQLite

- Start the server with SQLite for backend:
    - See [Scenario 3: MLflow on localhost with Tracking Server](https://www.mlflow.org/docs/latest/tracking.html#scenario-3-mlflow-on-localhost-with-tracking-server)


```
# both mlruns_db.sqlite & mlruns will be stored in the current folder
mlflow server --backend-store-uri sqlite:///mlruns_db.sqlite --default-artifact-root ./mlruns

```
