# Locust

## Usage

1. Install poetry with dev dependencies.
2. Create a sketch-map with the database you want to do tests with locust.
3. Save the sketch-map you want to digitize in `/locust/sketch-map.png` or change the config.
4. Change config if necessary
5. Run `locust` and open http://localhost:8089

More information: https://docs.locust.io

## Configuration

At the moment you can set these env variables:
```bash
LOCUST_NUM_FILES=1
LOCUST_MAP_FILENAME="sketch-map.png"

# To be added:
#     host = 'http://localhost:8081'
#     wait_time = constant(6)
#     api_status_wait_time = 5
#     api_status_retries = 30
```
