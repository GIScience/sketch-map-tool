# Configuration

The Sketch Map Tool can be configured using a configuration file.

## Configuration File

The default path of the configuration file is `config/config.toml`.
A sample configuration file can be found in the same directory: `config/sample.config.toml`.
All configuration files in this directory (`config`) will be ignored by Git.
To change the default configuration file path for OQT set the environment variable `SMT_CONFIG` to the desired path.

To create a new configuration file simply copy the sample configuration file and change the values.

```bash
cp sample.config.toml config.toml
```

## Required Configuration

All lot of configuration values come with defaults. Required configuration values are:
- `neptune_api_token`
- `esri-api-key`

## Configuration for Docker Compose

For running the services using Docker Compose set broker URL and result backend to:

```toml
broker-url = "redis://redis:6379"
result-backend = "db+postgresql://smt:smt@postgres:5432"
```
