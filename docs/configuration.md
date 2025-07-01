# Configuration

The Sketch Map Tool can be configured using a configuration file.

## Configuration File

The default path of the configuration file is `config/config.toml`.
A sample configuration file can be found in the same directory: `config/sample.config.toml`.
All configuration files in this directory (`config`) will be ignored by Git.
To change the default configuration file path set the environment variable `SMT_CONFIG` to the desired path.

To create a new configuration file simply copy the sample configuration file and change the values.

```bash
cp config/sample.config.toml config/config.toml
```

## Default Configuration

For a list of all configuration variables and their default values please take a look at [config.py](sketch_map_tool/config.py).

All lot of configuration values come with defaults.

For running the services using Docker Compose set broker URL and result backend to:

```toml
broker-url = "redis://redis:6379"
result-backend = "db+postgresql://smt:smt@postgres:5432"
```

## Misc

### ArcGIS/ESRI API Key

To retrieve up-to-date attribution an ArcGIS/ESRI API key is needed.
For local development you do not need one.
To get an ArcGIS/ESRI API key sign-up for [ArcGIS Location Platform](https://location.arcgis.com/sign-up/)
and follow [this tutorial](https://developers.arcgis.com/documentation/security-and-authentication/api-key-authentication/tutorials/create-an-api-key/).

Notes:
1. During registration enter your username into the "Your portal URL" and "Your portal display name" fields (not `heigit`).
2. During API key generation keep the referrer field empty.
