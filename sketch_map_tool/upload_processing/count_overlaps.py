import os
import pathlib
import shutil
from io import BytesIO
from tempfile import NamedTemporaryFile
from typing import List, Tuple
from zipfile import ZipFile

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import processing
from processing.core.Processing import Processing
from processing.script import ScriptUtils
from qgis.core import (
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsProject,
    QgsVectorLayer,
)


def create_qgis_project(markings: BytesIO) -> Tuple[BytesIO, BytesIO]:
    """
    Create a QGIS project with the detected markings as layer, run a QGIS script to count the overlapping markings
    (from different sketch maps) per colour, resulting in an additional layer in the project.

    :param markings: GeoJSON with the detected markings.
    :return: (ZIP file containing the QGIS project and both layers as GeoJSONs, GeoJSON of the overlap counts).
    """
    project = QgsProject()
    project.setTitle("Sketch Map Tool Results")
    reference_system = QgsCoordinateReferenceSystem("EPSG:4326")
    project.setCrs(reference_system)

    # Add detected markings as layer
    infile = NamedTemporaryFile(prefix="markings_", suffix=".geojson")
    with open(infile.name, "wb") as f:
        f.write(markings.read())
    layer = QgsVectorLayer(infile.name, "Markings", "ogr")
    project.addMapLayer(layer)

    # Add custom QGIS scripts to processing toolbox:
    Processing.initialize()
    scripts_path = pathlib.Path(__file__).parent.resolve() / "qgis_scripts"
    qgis_scripts_path = ScriptUtils.defaultScriptsFolder()
    added_scripts = False
    for filename in os.listdir(scripts_path):
        if filename not in os.listdir(qgis_scripts_path):
            shutil.copy(
                os.path.join(scripts_path, filename),
                os.path.join(qgis_scripts_path, filename),
            )
            added_scripts = True

    if added_scripts:
        QgsApplication.processingRegistry().providerById("script").refreshAlgorithms()

    # Run the overlapping count script
    result_file = NamedTemporaryFile(prefix="overlap_counts_", suffix=".geojson")
    processing.run(
        "script:split_count_merge",
        {
            "inlayer": infile.name,
            "OutputLayer": result_file.name,
            "uniqueidfield": "color",
        },
    )

    layer_result = QgsVectorLayer(result_file.name, "Overlap Counts", "ogr")
    project.addMapLayer(layer_result)

    outfile = NamedTemporaryFile(suffix=".qgs")
    project.write(outfile.name)
    buffer_project = BytesIO()
    buffer_overlaps = (
        BytesIO()
    )  # Both included in the project ZIP and returned separately for the heatmap generation
    with (
        ZipFile(buffer_project, "w") as zip_file,
        open(infile.name, "rb") as f_markings,
        open(outfile.name, "rb") as f_qgis,
        open(result_file.name, "rb") as f_result,
    ):
        zip_file.writestr(infile.name.replace("tmp/", "./"), f_markings.read())
        zip_file.writestr(result_file.name.replace("tmp/", "./"), f_result.read())
        zip_file.writestr("project.qgs", f_qgis.read())
        f_result.seek(0)
        buffer_overlaps.write(f_result.read())
    buffer_project.seek(0)
    buffer_overlaps.seek(0)
    return buffer_project, buffer_overlaps


def generate_heatmaps(
    geojson_path, lon_min, lat_min, lon_max, lat_max, bg_img_path
) -> List[Tuple[str, BytesIO]]:
    """
    Create heatmaps covering the extent given in 'lon_min', ..., 'lat_max' arguments, based on the
    'COUNT' data in the GeoJSON referred to with 'geojson_path' for each colour (as stored in the property 'color').

    :param geojson_path: Path to a GeoJSON containing a 'COUNT' and a 'color' property for all features.
    :param lon_min: Longitude in web mercator of the lower left corner of the extent.
    :param lat_min: Latitude in web mercator of the lower left corner of the extent.
    :param lon_max: Longitude in web mercator of the upper right corner of the extent.
    :param lat_max: Latitude in web mercator of the upper right corner of the extent.
    :param bg_img_path: Path to the map image to be used as background for the heatmaps.
    :return: JPGs of the heatmaps for each colour of detected markings and the names of the
             corresponding colours.
    """
    df_geojson = gpd.read_file(geojson_path)
    results = []
    for colour in df_geojson["color"].unique():
        df_col = df_geojson[df_geojson["color"] == colour]
        fig = plt.figure()
        ax = fig.subplots()

        xlim = [lon_min, lon_max]
        ylim = [lat_min, lat_max]
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)

        img = plt.imread(bg_img_path)
        ax.imshow(img, extent=[lon_min, lon_max, lat_min, lat_max])

        # Plot heatmanp
        df_col.plot(column="COUNT", cmap="cividis", ax=ax)

        # Add legend limited to integer values in the observed range of counts
        plt.colorbar(
            ax.get_children()[1],
            ax=ax,
            ticks=np.arange(
                np.min(np.asarray(df_col["COUNT"]).astype(int)),
                np.max(np.asarray(df_col["COUNT"]).astype(int)) + 1,
            ),
        )
        result_buffer = BytesIO()
        fig.savefig(result_buffer, format="jpg")
        result_buffer.seek(0)
        results.append((colour, result_buffer))
    return results
