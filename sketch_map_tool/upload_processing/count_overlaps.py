from io import BytesIO
from tempfile import NamedTemporaryFile
from qgis.core import (QgsProject, QgsVectorLayer, QgsCoordinateReferenceSystem, QgsApplication,
                       QgsProcessingFeatureSourceDefinition, QgsProcessingFeedback)
from qgis.analysis import QgsNativeAlgorithms
from zipfile import ZipFile
import processing
from processing.core.Processing import Processing
from processing.script import ScriptUtils
import os
import shutil
import pathlib


def create_qgis_project(markings: BytesIO):
    project = QgsProject()
    project.setTitle("Sketch Map Tool Results")
    infile = NamedTemporaryFile(suffix=".geojson")
    with open(infile.name, "wb") as f:
        f.write(markings.read())
    layer = QgsVectorLayer(infile.name, "Markings", 'ogr')
    project.addMapLayer(layer)
    reference_system = QgsCoordinateReferenceSystem("EPSG:4326")
    project.setCrs(reference_system)
    result_file = NamedTemporaryFile(suffix=".geojson")
    Processing.initialize()

    # Add custom QGIS scripts to processing toolbox:
    scripts_path = pathlib.Path(__file__).parent.resolve() / "qgis_scripts"
    qgis_scripts_path = ScriptUtils.defaultScriptsFolder()

    added_scripts = False
    for filename in os.listdir(scripts_path):
        if filename not in os.listdir(qgis_scripts_path):
            shutil.copy(os.path.join(scripts_path, filename), os.path.join(qgis_scripts_path, filename))
            added_scripts = True

    if added_scripts:
        QgsApplication.processingRegistry().providerById("script").refreshAlgorithms()

    processing.run("script:split_count_merge", {
        'inlayer': infile.name,
        'OutputLayer': result_file.name,
        'uniqueidfield': "color",
        # 'OUTPUT': 'memory:'
    })
    layer_result = QgsVectorLayer(result_file.name, "Overlap Counts", 'ogr')
    project.addMapLayer(layer_result)
    outfile = NamedTemporaryFile(suffix=".qgs")
    project.write(outfile.name)
    buffer = BytesIO()
    with (ZipFile(buffer, "w") as zip_file, open(infile.name, "rb") as f_markings, open(outfile.name, "rb") as f_qgis,
          open(result_file.name, "rb") as f_result):
        zip_file.writestr(infile.name.replace("tmp/", "./"), f_markings.read())
        zip_file.writestr(result_file.name.replace("tmp/", "./"), f_result.read())
        zip_file.writestr(f"project.qgs", f_qgis.read())
    buffer.seek(0)
    return buffer
