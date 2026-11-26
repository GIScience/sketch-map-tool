from dataclasses import dataclass
from io import BytesIO
from typing import Annotated, Literal

import shapely
from numpy.typing import NDArray
from PIL import Image
from pydantic import (
    UUID4,
    Base64Bytes,
    BaseModel,
    BeforeValidator,
    Field,
    field_validator,
)
from pydantic_extra_types import Color

from sketch_map_tool.helpers import to_array


@dataclass(frozen=True)
class Bbox:
    """Bounding Box in WGS 84 / Pseudo-Mercator (EPSG:3857)."""

    # Be aware that the argument order is relevant to the API and the JavaScript client.
    # Keep the order in sync with the client.

    lon_min: float
    lat_min: float
    lon_max: float
    lat_max: float

    @property
    def centroid(self) -> shapely.geometry.Point:
        """The coordinates of the centroid."""
        return shapely.geometry.box(
            self.lon_min,
            self.lat_min,
            self.lon_max,
            self.lat_max,
        ).centroid

    @property
    def wkt(self) -> str:
        """The coordinates of the centroid."""
        return shapely.geometry.box(
            self.lon_min,
            self.lat_min,
            self.lon_max,
            self.lat_max,
        ).wkt

    def __str__(self) -> str:
        return f"{self.lon_min},{self.lat_min},{self.lon_max},{self.lat_max}"


@dataclass(frozen=True, kw_only=True)
class Size:
    """Print box size in dots [pt].

    This is useful to determine the OGC-WMS params 'WIDTH' and 'HEIGHT'.
    """

    width: float
    height: float

    def __str__(self):
        return f"{self.width}x{self.height}"

    def asdict(self):
        return {"width": self.width, "height": self.height}


@dataclass(frozen=True)
class PaperFormat:
    """Properties of sketch maps to be printed on a certain paper format.

    Attributes:
        title: Name of the paper format
        width: Width of the paper [cm]
        height: Height of the paper [cm]
        right_margin: Width of the margin [cm]
        map_margin: Width of the margin around the map [cm]
        font_size: Font size [pt]
        qr_scale: Scale factor of the QR-code
        compass_scale: Scale factor of the compass
        marker_scale: Scale factor of the aruco markers
        scale_height: Height of the scale [px].
        scale_relative_xy: Position of the scale relative to the map frame width or
            height respectively
        scale_background_params: (x relative to scale, y relative to scale,
            length additional to scale, height)
        scale_distance_to_text: Distance from the scale bar
            to the text describing it [px]
        qr_y: Vertical distance from origin to the QR-code [cm]
        indent: Indentation of the margin's content relative to the map area [cm]
        qr_contents_distances_not_rotated: Tuple of distances [cm]
            (Vertical distance from the QR-code contents in text form to the position
            of the copyright notice, Indentation additional to the calculated base
            indentation of all rotated contents)
        qr_contents_distance_rotated:
            Horizontal distance from the map area additional to the calculated base
            indentation of all rotated contents [cm]
    """

    title: str
    width: float
    height: float
    right_margin: float
    map_margin: float
    font_size: int
    qr_scale: float
    compass_scale: float
    marker_scale: float
    scale_height: int
    scale_relative_xy: tuple[int, int]
    scale_background_params: tuple[int, int, int, int]
    scale_distance_to_text: int
    qr_y: float
    indent: float
    qr_contents_distances_not_rotated: tuple[int, int]
    qr_contents_distance_rotated: int

    def __str__(self):
        return self.title


@dataclass()
class LiteratureReference:
    citation: str
    img_src: str | None = None
    url: str | None = None


class MapFrame(BaseModel):
    uuid: UUID4
    map_image: bytes
    bbox_3857: Bbox
    bbox_4326: Bbox
    format: str
    orientation: Literal["landscape", "portrait"]
    layer: str

    def map_image_as_image(self) -> Image.Image:
        return Image.open(BytesIO(self.map_image))

    def map_image_as_array(self) -> NDArray:
        return to_array(self.map_image)


PNG_DATA_URL_PREFIX = "data:image/png;base64"
MAX_PNG_SIZE = 128 * 128


def strip_data_url_prefix(v: str) -> str:
    if isinstance(v, str) and v.startswith("data:"):
        header, sep, payload = v.partition(",")
        if sep and header == PNG_DATA_URL_PREFIX:
            return payload
    raise ValueError("Not a valid data:image/png;base64 data URL")


DataUrlBase64Bytes = Annotated[Base64Bytes, BeforeValidator(strip_data_url_prefix)]


class LegendEntry(BaseModel):
    """Legend entry as rendered and sent by the client.

    See client-src/digitize-preview/legend.ts.
    """

    color: Color
    hex: Color
    type: Literal["point", "polygon"]
    count: int = Field(ge=0)
    label: str = Field(max_length=200)
    image: DataUrlBase64Bytes
    width: float = Field(ge=0, le=128)
    height: float = Field(ge=0, le=128)

    @field_validator("image")
    @classmethod
    def validate_image(cls, value: DataUrlBase64Bytes) -> DataUrlBase64Bytes:
        try:
            img = Image.open(BytesIO(value))
            img.verify()
        except Exception as error:
            raise ValueError("Not a valid PNG image") from error

        if max(img.size) > MAX_PNG_SIZE:
            raise ValueError("Image is too large")

        return value


class Legend(BaseModel):
    title: str = Field(default="", max_length=100)
    entries: list[LegendEntry]
