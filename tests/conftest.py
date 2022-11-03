import pytest


@pytest.fixture
def bbox():
    return [964598.2387041415, 6343922.275917276, 967350.9272435782, 6346262.602545459]


@pytest.fixture
def size():
    return {"width": 1867, "height": 1587}
