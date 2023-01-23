# TODO install locust
import logging
import os
from time import sleep
from uuid import UUID

from locust import HttpUser, constant, run_single_user, task

logging.basicConfig()


def validate_uuid(uuid: str):
    try:
        _ = UUID(uuid, version=4)
    except ValueError:
        raise (ValueError('"{}" is not valid a UUID!'.format(uuid)))


class WorkflowCycle(HttpUser):
    host = "http://localhost:8081"
    wait_time = constant(6)
    api_status_wait_time = 5
    api_status_retries = 30

    @task
    def create(self):
        payload = {
            "format": "A4",
            "orientation": "landscape",
            "bbox": "[964881.9316858181,6343777.762160674,967129.3396389671,6345658.909256095]",
            "bboxWGS84": "[8.667681866041383,49.40450221498196,8.687870675181037,49.41549716938161]",
            "size": '{"width":1716,"height":1436}',
            "scale": "8391.039601898965",
        }
        create_post = self.client.post("/create/results", data=payload)
        create_uuid = create_post.url.split("/")[-1]
        validate_uuid(create_uuid)
        download_url = self.status_loop(create_uuid, "sketch-map")
        request_name = "/api/download/[uuid]/sketch-map"
        self.client.get(download_url, name=request_name)

    @task
    def digitize(self):
        num_files = os.getenv("LOCUST_NUM_FILES", default=1)
        map_filename = os.getenv("LOCUST_MAP_FILENAME", default="sketch-map.png")
        files = [("file", open(map_filename, "rb")) for _ in range(num_files)]
        digitize_post = self.client.post("/digitize/results", files=files)
        digitize_uuid = digitize_post.url.split("/")[-1]
        validate_uuid(digitize_uuid)
        for result_type in ("raster-results", "vector-results"):
            download_url = self.status_loop(digitize_uuid, result_type)
            request_name = "/api/download/[uuid]/{}".format(result_type)
            self.client.get(download_url, name=request_name)

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
