from PIL.PngImagePlugin import PngImageFile

from sketch_map_tool.wms import client


def test_get_map_image():
    response = client.get_map_image(
        bbox=[
            964598.2387041415,
            6343922.275917276,
            967350.9272435782,
            6346262.602545459,
        ],
        width=1867,
        height=1587,
    )
    assert response.status_code == 200


def test_as_image():
    response = client.get_map_image(
        bbox=[
            964598.2387041415,
            6343922.275917276,
            967350.9272435782,
            6346262.602545459,
        ],
        width=1867,
        height=1587,
    )
    image = client.as_image(response)
    assert isinstance(image, PngImageFile)
