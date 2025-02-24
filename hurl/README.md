# README

[Hurl](https://hurl.dev/) is used to stress test a running instance of the Sketch Map Tool.

1. A sketch map is created and saved to disk as PDF
2. Convert the PDF to an image
3. Upload image 12 times in parallel to digitize sketches

The uploaded image does not contain any sketches. This is not important because the machine learning pipeline is executed nonetheless.

We upload 12 images in parallel because Celery is started with a concurrency setting of 6. We want to test how Celery handles more than 6 requests at the same time.

```bash
hurl --test create.hurl
magick -density 300 sketch-map.pdf sketch-map.png
hurl --test --jobs 12 --repeat 12 digitize.hurl
```
