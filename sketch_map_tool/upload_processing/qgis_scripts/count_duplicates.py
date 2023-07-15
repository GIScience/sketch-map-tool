"""
Count duplicate, i.e. overlapping, features of input layer.
"""

from PyQt5.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterString)
import processing

from qgis.core import QgsField, QgsFeature
from PyQt5.QtCore import QVariant


# TODO: Refactor
class CountDuplicates(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'
    ID_FIELD = 'ID_FIELD'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return CountDuplicates()

    def name(self):
        return 'count_duplicates'

    def displayName(self):
        return self.tr('Count duplicates')

    def group(self):
        return self.tr('')

    def groupId(self):
        return ''

    def shortHelpString(self):
        return self.tr("Count Duplicates in input layer.")

    def initAlgorithm(self, config=None):
        # Add the input vector features source
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Input layer'),
                [QgsProcessing.TypeVectorAnyGeometry]
            )
        )

        # Add a feature sink in which to store our processed features (this usually takes the form of a
        # newly created vector layer)
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Output layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        # Retrieve the feature source and sink
        source = self.parameterAsSource(
            parameters,
            self.INPUT,
            context
        )

        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        # Create the output layer
        out_fields = source.fields()
        out_fields.append(QgsField("COUNT", QVariant.Int, '', 10, 0))
        
        # Add id fields, used to TODO
        name_index = source.fields().indexOf("name")
        values = source.uniqueValues(name_index)
        for id_value in values:
            out_fields.append(QgsField(str(id_value), QVariant.Int, '', 10, 0))
        out_fields.remove(name_index)
        # TODO: Contents of out_fields now -> Can the initialisation be made more clearly?

        # The 'dest_id' variable is used to uniquely identify the feature sink
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            out_fields,
            source.wkbType(),
            source.sourceCrs()
        )
        
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        features = source.getFeatures()

        for i, feature in enumerate(features):
            attributes = feature.attributes()
            attributes.remove(name_index)
            attributes += [0] * (len(out_fields) - len(attributes))  # TODO: Why?

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
        return {self.OUTPUT: dest_id}
