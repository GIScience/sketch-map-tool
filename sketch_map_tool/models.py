import base64
import binascii
from dataclasses import dataclass
from io import BytesIO
from typing import Annotated, Literal

import shapely
from numpy.typing import NDArray
from PIL import Image
from pydantic import UUID4, BaseModel, Field, TypeAdapter, field_validator

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


PNG_DATA_URL_PREFIX = "data:image/png;base64,"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_LEGEND_IMAGE_BYTES = 200_000
MAX_LEGEND_ENTRIES = 50


class LegendEntry(BaseModel):
    """Legend entry as rendered and sent by the client.

    See client-src/digitize-preview/legend.ts. Comes from user input: validate
    defensively.
    """

    color: str = Field(max_length=50)
    hex: str = Field(max_length=20)
    type: Literal["point", "polygon"]
    count: int = Field(ge=0)
    label: str = Field(max_length=100)
    # PNG data URL of the symbol, empty if the client could not draw it
    image: str = ""
    # size of the symbol in CSS pixels
    width: float = Field(ge=0, le=500)
    height: float = Field(ge=0, le=500)

    @field_validator("image")
    @classmethod
    def validate_image(cls, value: str) -> str:
        if value == "":
            return value
        if not value.startswith(PNG_DATA_URL_PREFIX):
            raise ValueError("image must be a PNG data URL")
        # base64 needs 4 characters per 3 bytes
        if len(value) - len(PNG_DATA_URL_PREFIX) > MAX_LEGEND_IMAGE_BYTES * 4 / 3 + 4:
            raise ValueError("image is too large")
        try:
            data = base64.b64decode(value[len(PNG_DATA_URL_PREFIX) :], validate=True)
        except binascii.Error as error:
            raise ValueError("image is not valid base64") from error
        if not data.startswith(PNG_SIGNATURE):
            raise ValueError("image is not a PNG")
        return value

    def image_bytes(self) -> bytes | None:
        """The decoded PNG image, None if there is none."""
        if not self.image:
            return None
        return base64.b64decode(self.image[len(PNG_DATA_URL_PREFIX) :])


LegendEntries = Annotated[list[LegendEntry], Field(max_length=MAX_LEGEND_ENTRIES)]
legend_entries_adapter: TypeAdapter[list[LegendEntry]] = TypeAdapter(LegendEntries)


class Legend(BaseModel):
    title: str = ""
    entries: LegendEntries = []
