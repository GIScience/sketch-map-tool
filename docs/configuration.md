# Configuration

The Sketch Map Tool can be configured using a configuration file or environment variables. Configuration
values from environment variables have precedence over values from the configuration
file.

Below is a table listing all possible configuration variables.

| Configuration Variable Name | Environment Variable Name | Configuration File Name | Default Value                   | Description                                                                  |
| --------------------------- | ------------------------- | ----------------------- | ------------------------------- | ---------------------------------------------------------------------------- |
| Configuration File Path     | `SMT-CONFIG`              | -                       | `config/config.yaml`            | Absolute path to the configuration file                                      |
| Data Directory              | `SMT-DATA-DIR`            | `data-dir`              | `data`                          | Absolute path to the directory for raster files                              |
| User Agent                  | `SMT-USER-AGENT`          | `user-agent`            | `sketch-map-tool/{version}`     | User-Agent header for requests to third-party servics the ohsome API         |


## Configuration File

The default path of the configuration file is `config/config.toml`.
A sample configuration file can be found in the same directory: `config/sample.config.toml`.
All configuration files in this directory (`config`) will be ignored by Git. To change the default configuration file path for OQT set the environment variable `SMT-CONFIG` to the desired path.

To create a new configuration file simply copy the sample configuration file and change the values.

```
cp sample.config.toml config.toml
```
