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
        
        # Add id fields
        id_idx = source.fields().indexOf('name')
        values = source.uniqueValues(id_idx)
        for id_value in values:
            out_fields.append(QgsField("{}".format(id_value), QVariant.Int, '', 10, 0))
        out_fields.remove(id_idx)

        # The 'dest_id' variable is used to uniquely identify the feature sink
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            out_fields,
            source.wkbType(),
            source.sourceCrs()
        )
        
        feedback.pushInfo('CRS is {}'.format(source.sourceCrs().authid()))

        # If sink was not created, throw an exception to indicate that the algorithm
        # encountered a fatal error.
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        # Compute the number of steps to display within the progress bar and
        # get features from source
        total = 100.0 / source.featureCount() if source.featureCount() else 0
        features = [feat for feat in source.getFeatures()]

        for current, feature in enumerate(features):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            # make attribute list
            inAttr = feature.attributes()
            del inAttr[id_idx]
            inAttr += [0] * (len(out_fields) - len(inAttr))

            count = 0
            add_feature = True

            for other_current, other_feature in enumerate(features):
                if feature.geometry().equals(other_feature.geometry()):
                    feature_id = other_feature.attributes()[id_idx]
                    inAttr[out_fields.indexOf("{}".format(feature_id))] += 1
                    count += 1
                    # duplicate feature already added?
                    if current > other_current:
                        add_feature = False
            # create new feature
            out_feature = QgsFeature()
            # set attributes and geometry
            inAttr[out_fields.indexOf("COUNT")] = count
            out_feature.setAttributes(inAttr)
            out_feature.setGeometry(feature.geometry())

            # Add a feature in the sink
            if add_feature:
                sink.addFeature(out_feature, QgsFeatureSink.FastInsert)

            # Update the progress bar
            feedback.setProgress(int(current * total))

        return {self.OUTPUT: dest_id}
