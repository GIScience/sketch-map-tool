"""
For each colour that has been used for markings, count overlapping features,
i.e. overlapping markings in that colour from different sketch maps.
"""

import processing
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingMultiStepFeedback,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterString,
    QgsProcessingParameterVectorLayer,
)


# TODO: Refactor
class Split_count_merge(QgsProcessingAlgorithm):
    def initAlgorithm(self, config=False):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                "inlayer",
                "Input Layer",
                types=[QgsProcessing.TypeVectorPolygon],
                defaultValue=None,
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                "uniqueidfield",
                "Colour field name",
                multiLine=False,
                defaultValue="color",
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                "OutputLayer",
                "Output Layer",
                type=QgsProcessing.TypeVectorAnyGeometry,
                createByDefault=True,
                defaultValue=None,
            )
        )

    def processAlgorithm(self, parameters, context, model_feedback):
        feedback = QgsProcessingMultiStepFeedback(1, model_feedback)
        results = {}
        outputs = {}

        alg_params = {
            "FIELDS": parameters["uniqueidfield"],
            "INPUT": parameters["inlayer"],
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            "OUTPUT_HTML_FILE": QgsProcessing.TEMPORARY_OUTPUT,
        }
        unique_id_values = processing.run(
            "qgis:listuniquevalues",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )["UNIQUE_VALUES"].split(";")
        out_layers = []
        for value in unique_id_values:
            alg_params = {
                "FIELD": parameters["uniqueidfield"],
                "INPUT": parameters["inlayer"],
                "OPERATOR": 0,
                "VALUE": value,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            }

            # TODO: What does this script do?
            extracted_by_attribute = processing.run(
                "native:extractbyattribute",
                alg_params,
                context=context,
                feedback=feedback,
                is_child_algorithm=True,
            )["OUTPUT"]

            alg_params = {
                "INPUT": extracted_by_attribute,
                "OVERLAY": None,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            }

            union = processing.run(
                "native:union",
                alg_params,
                context=context,
                feedback=feedback,
                is_child_algorithm=True,
            )["OUTPUT"]
            feedback.setCurrentStep(2)
            if feedback.isCanceled():
                return {}

            alg_params = {"INPUT": union, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT}
            # Run custom count_duplicates script (also needs to be added to the QGIS processing toolbox before
            # running this one)
            # TODO: Add code from second script here
            overlap_counts = processing.run(
                "script:count_duplicates",
                alg_params,
                context=context,
                feedback=feedback,
                is_child_algorithm=True,
            )["OUTPUT"]
            out_layers.append(overlap_counts)

        # Merge vector layers
        alg_params = {
            "CRS": parameters["inlayer"],
            "LAYERS": out_layers,
            "OUTPUT": parameters["OutputLayer"],
        }

        results["OutputLayer"] = processing.run(
            "native:mergevectorlayers",
            alg_params,
            context=context,
            feedback=feedback,
            is_child_algorithm=True,
        )["OUTPUT"]
        return results

    def name(self):
        return "split_count_merge"

    def displayName(self):
        return "split_count_merge"

    def group(self):
        return ""

    def groupId(self):
        return ""

    def shortHelpString(self):
        return "Split input layer by unique colours. Count duplicates for every unique value found. Merge resulting layers into final Output Layer, containing counts of overlapping features for each unique attribute value in specified id_field."

    def createInstance(self):
        return Split_count_merge()
