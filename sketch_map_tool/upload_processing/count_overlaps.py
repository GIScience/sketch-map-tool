from io import BytesIO
from tempfile import NamedTemporaryFile
from qgis.core import (QgsProject, QgsVectorLayer, QgsCoordinateReferenceSystem, QgsApplication,
                       QgsProcessingFeatureSourceDefinition, QgsProcessingFeedback)
from qgis.analysis import QgsNativeAlgorithms
from zipfile import ZipFile
import processing
from processing.core.Processing import Processing


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
    inter_file = NamedTemporaryFile(suffix=".geojson")
    Processing.initialize()
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
    buffered_layer = processing.run("native:buffer", {
        'INPUT': infile.name,
        'DISTANCE': 1.5,
        'SEGMENTS': 5,
        'END_CAP_STYLE': 0,
        'JOIN_STYLE': 0,
        'MITER_LIMIT': 2,
        'DISSOLVE': False,
        'OUTPUT': inter_file.name,
        # 'OUTPUT': 'memory:'
    })['OUTPUT']
    outfile = NamedTemporaryFile(suffix=".qgs")
    project.write(outfile.name)
    buffer = BytesIO()
    with (ZipFile(buffer, "w") as zip_file, open(infile.name, "rb") as f_markings, open(outfile.name, "rb") as f_qgis,
          open(inter_file.name, "rb") as f_inter):
        zip_file.writestr(infile.name.replace("tmp/", "./"), f_markings.read())
        zip_file.writestr(inter_file.name.replace("tmp/", "./"), f_inter.read())
        zip_file.writestr(f"project.qgs", f_qgis.read())
    buffer.seek(0)
    return buffer
