# SketchMapTool Helm chart
## Database configuration
SketchMapTool requires a postgres database to run.
- Default config: A database will be deployed along side SMT with default passwords.
- Keep the builtin postgres but set your own passwords: the keys under `postgres.userDatabase` and `postgres.settings.superuserPassword` allow you to provide alternative values for user, database and passwords either directly or via an existing secret. See values.yaml for details
- Supply your own database: Set `postgres.enabled` to `false`. Provide the address of your external postgres host at `postgres.connectionString`. The user, database and password settings will still be used as above. Set them either directly or via an existing secret.

## Cache configuration
SketchMapTool requires a redis cache to run.
- Default config: A redis cache will be deployed along side SMT.
- Supply your own cache: Set `redis.enabled` to `false`. If your external redis cache requires a password to access you need to set this on the application yourself.

## External access
By default this chart deploys two services to kubernetes, flask and flower. These are not exposed outside the cluster unless you enable either ingress or httpRoute for them, depending on which API your cluster supports. If, for example, you want to expose flask with an ingress you should set `flask.ingress.enabled` to true and configure your ingress with the other options under `flask.ingress`.
