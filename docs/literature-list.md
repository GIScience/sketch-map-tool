# Literature List

On the `/about` page a list of "Related Publications" is displayed.

To facilitate the maintenance of this list, its generation is automated by reading from a JSON-File
called 'literature.json'.

This file can be found in the `./sketch_map_tool/data/` folder.

Each literature reference must at least have a `"citation"` text and can have an `"imgSrc"` and
a `"url"` property.

Example:

```json
[
  {
    "citation": "Klonner, C., Hartmann, M., Dischl, R., Djami, L., Anderson, L., Raifer, M., Lima-Silva, F., Degrossi, L. C., Zipf, A., de Albuquerque, J. P. (2021): The Sketch Map Tool Facilitates the Assessment of OpenStreetMap Data for Participatory Mapping, 10(3): 130. ISPRS International Journal of Geo-Information. 10:130.",
    "imgSrc": "ijgi-10-00130-g002.webp",
    "url": "https://doi.org/10.3390/ijgi10030130"
  }
]
```

## citation

This is a mandatory plain-text, which should be formatted as to be displayed.

## imgSrc

Optionally a `"imgSrc"` can be given to be used as preview image next to the reference.

This can be either a URL to a web resource starting with `"http://"` or `"https://"` or a local
image filename.

In case of a local file just use the filename without path in the `"imSrc"`. The local file should
be put in the folder `./sketch_map_tool/static/assets/images/about/publications/`.

A good size for the preview image would not be more than 300px in width.

## url

Optionally a `"url"` can be given that will be displayed as link and should point to the original
article.

