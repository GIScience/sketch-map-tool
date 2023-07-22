"""
For each colour that has been used for markings, count overlapping features,
i.e. overlapping markings in that colour from different sketch maps.
"""

import processing
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterString,
    QgsProcessingParameterVectorLayer,
)


# TODO: Refactor
class CountOverlaps(QgsProcessingAlgorithm):
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
                "colour_field",
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
        results = {}

        alg_params = {
            "FIELDS": parameters["colour_field"],
            "INPUT": parameters["inlayer"],
            "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            "OUTPUT_HTML_FILE": QgsProcessing.TEMPORARY_OUTPUT,
        }
        unique_colour_values = processing.run(
            "qgis:listuniquevalues",
            alg_params,
            context=context,
            is_child_algorithm=True,
        )["UNIQUE_VALUES"].split(";")
        out_layers = []
        for colour in unique_colour_values:
            alg_params = {
                "FIELD": parameters["colour_field"],
                "INPUT": parameters["inlayer"],
                "OPERATOR": 0,
                "VALUE": colour,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            }

            layer_current_colour = processing.run(
                "native:extractbyattribute",
                alg_params,
                context=context,
                is_child_algorithm=True,
            )["OUTPUT"]

            # Create separate features for overlaps and non-overlapping parts of features, i.e.
            # split features on overlaps and create an overlap feature for each feature involved
            # in the overlap
            alg_params = {
                "INPUT": layer_current_colour,
                "OVERLAY": None,
                "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT,
            }
            union = processing.run(
                "native:union",
                alg_params,
                context=context,
                is_child_algorithm=True,
            )["OUTPUT"]

            alg_params = {"INPUT": union, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT}

            # Create the output layer fields
            out_fields = source.fields()
            out_fields.append(QgsField("COUNT", QVariant.Int, "", 10, 0))

            # Add fields identifying different sketch maps, i.e. the filenames
            # They will be used to indicate to which sketch maps each part of the markings belongs to
            name_index = source.fields().indexOf("name")
            unique_ids = source.uniqueValues(name_index)
            sketch_map_indicator_fields_indices = []
            for id_ in unique_ids:
                sketch_map_indicator_fields_indices.append(len(out_fields))
                out_fields.append(QgsField(str(id_), QVariant.Int, "", 10, 0))
            out_fields.remove(name_index)

            # The 'dest_id' variable is used to uniquely identify the feature sink
            (sink, dest_id) = self.parameterAsSink(
                parameters,
                self.OUTPUT,
                context,
                out_fields,
                source.wkbType(),
                source.sourceCrs(),
            )

            if sink is None:
                raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

            features = source.getFeatures()

            for i, feature in enumerate(features):
                attributes = feature.attributes()
                del attributes[name_index]
                attributes += [0] * (len(out_fields) - len(attributes))  # Initialise new fields with zero

                count = 0
                add_feature = True

                for j, other_feature in enumerate(features):
                    if feature.geometry().equals(other_feature.geometry()):
                        feature_id = other_feature.attributes()[name_index]
                        attributes[out_fields.indexOf("{}".format(feature_id))] += 1
                        count += 1
                        if j >= i:  # duplicate feature not already added
                            out_feature = QgsFeature()
                            attributes[out_fields.indexOf("COUNT")] = count
                            out_feature.setAttributes(attributes)
                            out_feature.setGeometry(feature.geometry())
                            sink.addFeature(out_feature, QgsFeatureSink.FastInsert)

            for indicator_field_index in sketch_map_indicator_fields_indices:
                out_fields.remove(indicator_field_index)
            return {self.OUTPUT: dest_id}

            out_layers.append(overlap_counts)





        # Merge overlap count layers for different colours
        alg_params = {
            "CRS": parameters["inlayer"],
            "LAYERS": out_layers,
            "OUTPUT": parameters["OutputLayer"],
        }

        results["OutputLayer"] = processing.run(
            "native:mergevectorlayers",
            alg_params,
            context=context,
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
