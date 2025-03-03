# README

[Hurl](https://hurl.dev/) is used to stress test a running instance of the Sketch Map Tool.

Workflow:

1. A sketch map is created and saved to disk as PDF (by Hurl)
2. The PDF is converted to an image (by ImageMagick)
3. The image is uploaded 7 times in parallel (by Hurl)

The uploaded image does not contain any sketches. This is not important because the machine learning pipeline is executed nonetheless.

7 images are upload in parallel because Celery is started with a concurrency setting of 6 (see [`compose.yaml`](/compose.yaml)). The purpose is to see how Celery handles more then 6 requests at the same time given the memory limits specified in the Docker Compose file.

## Usage

```bash
hurl --test create.hurl  # outputs sketch-map.pdf
magick -density 300 sketch-map.pdf sketch-map.png
hurl --test --jobs 7 --repeat 7 digitize.hurl  # uploads sketch-map.png
```
