from PyQt5.QtCore import QObject, pyqtSignal

import src.backend.layers as beLayers

class Group(QObject):

    referenceChanged = pyqtSignal()
    templateAdded = pyqtSignal()
    templateRemoved = pyqtSignal()

    def __init__(self):
        super().__init__()

        self._reference: beLayers.Layer = None
        self._templates: list[beLayers.Layer] = []

        self._dirty = True
        self.referenceChanged.connect(self.setDirty)
        self.templateAdded.connect(self.setDirty)
    

    def dirty(self):
        return self._dirty

    def setClean(self):
        self._dirty = False

    def setDirty(self):
        self._dirty = True
    
    
    def referenceLayer(self):
        return self._reference

    def setReferenceLayer(self, layer):
        if (layer is None
            or not isinstance(layer, beLayers.Layer)
            or self._reference == layer
        ):
            return

        if self._reference is not None:
            self._reference.maskChanged.disconnect(self.setDirty)

        layer.maskChanged.connect(self.setDirty)
        self._reference = layer
        self.referenceChanged.emit()
    

    def templateLayers(self):
        return self._templates

    def addTemplateLayer(self, layer):
        if (layer is None
            or not isinstance(layer, beLayers.Layer)
            or layer in self._templates
        ):
            return
        
        layer.maskChanged.connect(self.setDirty)
        self._templates.append(layer)
        self.templateAdded.emit()
    

    def removeTemplateLayer(self, layer):
        if (layer is None
            or not isinstance(layer, beLayers.Layer)
            or layer not in self._templates
        ):
            return
        
        layer.maskChanged.disconnect(self.setDirty)
        self._templates.remove(layer)
        self.templateRemoved.emit()
