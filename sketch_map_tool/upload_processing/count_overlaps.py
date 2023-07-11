from io import BytesIO
from tempfile import NamedTemporaryFile
from qgis.core import (QgsProject, QgsVectorLayer, QgsCoordinateReferenceSystem, QgsApplication,
                       QgsProcessingFeatureSourceDefinition, QgsProcessingFeedback)
from zipfile import ZipFile


def create_qgis_project(markings: BytesIO):
    project = QgsProject()
    project.setTitle("Sketch Map Tool Results")
    infile = NamedTemporaryFile(suffix=".geojson")
    with open(infile.name, "wb") as f:
        f.write(markings.read())
    layer = QgsVectorLayer(infile.name, f"Markings", 'ogr')
    project.addMapLayer(layer)
    reference_system = QgsCoordinateReferenceSystem("EPSG:4326")
    project.setCrs(reference_system)
    outfile = NamedTemporaryFile(suffix=".qgs")
    project.write(outfile.name)
    buffer = BytesIO()
    with ZipFile(buffer, "w") as zip_file, open(infile.name, "rb") as f_markings, open(outfile.name, "rb") as f_qgis:
        zip_file.writestr(infile.name.replace("tmp/", "./"), f_markings.read())
        zip_file.writestr(f"project.qgs", f_qgis.read())
    buffer.seek(0)
    return buffer
