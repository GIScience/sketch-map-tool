# Configuration

The Sketch Map Tool can be configured using a configuration file or environment variables. Configuration
values from environment variables have precedence over values from the configuration
file.

## Configuration File

The default path of the configuration file is `config/config.toml`.
A sample configuration file can be found in the same directory: `config/sample.config.toml`.
All configuration files in this directory (`config`) will be ignored by Git. To change the default configuration file path for OQT set the environment variable `SMT-CONFIG` to the desired path.

To create a new configuration file simply copy the sample configuration file and change the values.

```
cp sample.config.toml config.toml
```

## Required Configuration

Except of the API token (`SMT-NEPTUNE-API-TOKEN`) for neptune.ai all configuration values come with defaults for development purposes. Please make sure to configure the API token for your environment.
