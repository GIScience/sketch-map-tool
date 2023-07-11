from io import BytesIO
from tempfile import NamedTemporaryFile
from qgis.core import (QgsProject, QgsVectorLayer, QgsCoordinateReferenceSystem, QgsApplication,
                       QgsProcessingFeatureSourceDefinition, QgsProcessingFeedback)


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
    with open(outfile.name, "rb") as f:
        return BytesIO(f.read())
