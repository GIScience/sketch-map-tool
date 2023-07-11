"""
For each colour that has been used for markings, count overlapping features, i.e. overlapping markings in that
colour from different sketch maps.
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterString
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsMessageLog
from qgis.core import Qgis
import processing


# TODO: Refactor
class Split_count_merge(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=False):
        self.addParameter(QgsProcessingParameterVectorLayer('inlayer', 'Input Layer', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterString('uniqueidfield', 'Colour field name', multiLine=False, defaultValue='color'))
        self.addParameter(QgsProcessingParameterFeatureSink('OutputLayer', 'Output Layer', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        feedback = QgsProcessingMultiStepFeedback(1, model_feedback)
        results = {}
        outputs = {}

        alg_params = {
            'FIELDS': parameters['uniqueidfield'],
            'INPUT': parameters['inlayer'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT,
            'OUTPUT_HTML_FILE': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ListUniqueValues'] = processing.run('qgis:listuniquevalues', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        values = outputs['ListUniqueValues']['UNIQUE_VALUES']
        values = values.split(';')
        out_layers = []
        for value in values:
            # Extract by attribute
            alg_params = {
                'FIELD': parameters['uniqueidfield'],
                'INPUT': parameters['inlayer'],
                'OPERATOR': 0,
                'VALUE': value,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            try:
                outputs['ExtractByAttribute'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            except:
                QgsMessageLog.logMessage("ERROR AT RUNNING 'extractbyattribute' WITH value = "+str(value)+", parameters['inlayer'] = "+str(parameters['inlayer']), level=Qgis.Critical)
                raise Exception
            feedback.setCurrentStep(1)
            if feedback.isCanceled():
                return {}

            alg_params = {
                'INPUT': outputs['ExtractByAttribute']['OUTPUT'],
                'OVERLAY': None,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            try:
                outputs['Union'] = processing.run('native:union', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            except:
                QgsMessageLog.logMessage("ERROR AT RUNNING 'union' WITH outputs['ExtractByAttribute']['OUTPUT'] = "+str(outputs['ExtractByAttribute']['OUTPUT']), level=Qgis.Critical)
                raise Exception
            feedback.setCurrentStep(2)
            if feedback.isCanceled():
                return {}

            alg_params = {
                'INPUT': outputs['Union']['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            # Run custom count_duplicates script (also needs to be added to the QGIS processing toolbox before
            # running this one)
            try:
                outputs['CountDuplicates'] = processing.run('script:count_duplicates', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            except:
                QgsMessageLog.logMessage("ERROR AT RUNNING 'count_duplicates' WITH outputs['Union']['OUTPUT'] = "+str(outputs['Union']['OUTPUT']), level=Qgis.Critical)
                raise Exception
            out_layers.append(outputs['CountDuplicates']['OUTPUT'])
        
        # Merge vector layers
        alg_params = {
            'CRS': parameters['inlayer'],
            'LAYERS': out_layers,
            'OUTPUT': parameters['OutputLayer']
        }
        try:
            outputs['MergeVectorLayers'] = processing.run('native:mergevectorlayers', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        except:
            QgsMessageLog.logMessage("ERROR AT RUNNING 'mergevectorlayers' WITH out_layers = "+str(out_layers), level=Qgis.Critical)
            raise Exception
        results['OutputLayer'] = outputs['MergeVectorLayers']['OUTPUT']
        return results
        
    def name(self):
        return 'split_count_merge'

    def displayName(self):
        return 'split_count_merge'

    def group(self):
        return ''

    def groupId(self):
        return ''
    
    def shortHelpString(self):
        return 'Split input layer by unique colours. Count duplicates for every unique value found. Merge resulting layers into final Output Layer, containing counts of overlapping features for each unique attribute value in specified id_field.'

    def createInstance(self):
        return Split_count_merge()
