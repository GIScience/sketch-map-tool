# SketchMapTool Helm chart
## Result-backend database configuration
SketchMapTool requires a postgres database to run.
- Default config: A database will be deployed along side SMT with default passwords.
- Supply your own database: Set `postgres.enabled` to `false`. Provide the connection details of your external postgres host at `postgres.external`.

## Broker cache configuration
SketchMapTool requires a redis cache to run.
- Default config: A redis cache will be deployed along side SMT.
- Supply your own cache: Set `redis.enabled` to `false`. Provide the connection details of your external redis host at `redis.external.connectionString`.

## Generic configuration
Any additional config options can be supplied in toml format under the `customConfig` key.

## External access
By default this chart deploys two services to kubernetes, flask and flower. These are not exposed outside the cluster unless you enable either ingress or httpRoute for them, depending on which API your cluster supports. If, for example, you want to expose flask with an ingress you should set `flask.ingress.enabled` to true and configure your ingress with the other options under `flask.ingress`.
