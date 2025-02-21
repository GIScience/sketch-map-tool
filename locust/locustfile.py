import logging
import os
import time
from threading import Thread
from time import sleep
from uuid import UUID

from locust import HttpUser, constant, run_single_user, task

logging.basicConfig()
result_index = 0


def validate_uuid(uuid: str):
    try:
        _ = UUID(uuid, version=4)
    except ValueError:
        raise (ValueError('"{}" is not valid a UUID!'.format(uuid)))


def monitor_resource_use(wait_time_sec: int = 1):
    while True:
        os.system(
            'docker stats -a --no-stream --format "{{.Name}},{{.MemPerc}}" '
            ">> resource_log.csv"
        )
        time.sleep(wait_time_sec)


class WorkflowCycle(HttpUser):
    host = os.getenv("LOCUST_FLASK_HOST", default="http://localhost:8081")
    wait_time = constant(int(os.getenv("LOCUST_WAIT_TIME", default=6)))
    api_status_wait_time = int(os.getenv("LOCUST_API_STATUS_WAIT_TIME", default=5))
    api_status_retries = int(os.getenv("LOCUST_API_STATUS_RETRIES", default=30))
    thread_resource_monitoring = Thread(target=monitor_resource_use)
    thread_resource_monitoring.start()

    @task
    def create(self):
        global result_index
        payload = {
            "format": "A4",
            "orientation": "landscape",
            "bbox": (
                "[964881.9316858181,6343777.762160674,"
                "967129.3396389671,6345658.909256095]"
            ),
            "bboxWGS84": (
                "[8.667681866041383,49.40450221498196,"
                "8.687870675181037,49.41549716938161]"
            ),
            "size": '{"width":1716,"height":1436}',
            "scale": "8391.039601898965",
        }
        create_post = self.client.post("/create/results", data=payload)
        create_uuid = create_post.url.split("/")[-1]
        validate_uuid(create_uuid)

        if not os.path.exists("results"):
            os.mkdir("results")
        for result_type in ("sketch-map",):
            download_url = self.status_loop(create_uuid, result_type)
            request_name = f"/api/download/[uuid]/{result_type}"
            result = self.client.get(download_url, name=request_name)

            if result.status_code == 200:
                if not os.path.exists(f"results/{result_type}"):
                    os.mkdir(f"results/{result_type}")
                with open(f"results/{result_type}/file_{result_index}.pdf", "wb") as f:
                    f.write(result.content)
            else:
                raise ValueError(f"Unexpected status code: '{result.status_code}'")
            result_index += 1

    @task
    def digitize(self):
        global result_index
        num_files = int(os.getenv("LOCUST_NUM_FILES", default=1))
        map_filename = os.getenv("LOCUST_MAP_FILENAME", default="sketch-map.png")
        files = [("file", open(map_filename, "rb")) for _ in range(num_files)]
        digitize_post = self.client.post("/digitize/results", files=files)
        digitize_uuid = digitize_post.url.split("/")[-1]
        validate_uuid(digitize_uuid)
        for result_type in ("raster-results", "vector-results"):
            download_url = self.status_loop(digitize_uuid, result_type)
            request_name = "/api/download/[uuid]/{}".format(result_type)
            result = self.client.get(download_url, name=request_name)

            if result.status_code == 200:
                if not os.path.exists(f"results/{result_type}"):
                    os.mkdir(f"results/{result_type}")
                with open(f"results/{result_type}/file_{result_index}", "wb") as f:
                    f.write(result.content)
            else:
                raise ValueError(f"Unexpected status code: '{result.status_code}'")
            result_index += 1

    def status_loop(self, uuid: str, request_type: str):
        for _ in range(self.api_status_retries):
            request_name = "/api/status/[uuid]/{}".format(request_type)
            status_request = self.client.get(
                "/api/status/{}/{}".format(uuid, request_type), name=request_name
            )
            if status_request.status_code == 200:
                return status_request.json()["href"]
            sleep(self.api_status_wait_time)
        raise TimeoutError(
            "Reached the number of status retries ({}).".format(self.api_status_retries)
        )


# for debugging, normally you would only call "locust"
if __name__ == "__main__":
    run_single_user(WorkflowCycle)
