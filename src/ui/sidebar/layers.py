import re

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import src.util.loader as uLoader
import src.ui.misc.check as check
import src.ui.misc.button as button

CompositionMode = {
    "Normal": QPainter.CompositionMode_SourceOver,
    "Destination Over": QPainter.CompositionMode_DestinationOver,
    "Multiply": QPainter.CompositionMode_Multiply,
    "Overlay": QPainter.CompositionMode_Overlay,
    "Difference": QPainter.CompositionMode_Difference,
}

class LayerPane(QGroupBox):
    __instance = None

    def __init__(self):
        if LayerPane.__instance != None:
            raise Exception("Singleton")
        else:
            super().__init__("Layers")
            LayerPane.__instance = self
        
        self._widgets = {}
        self.initUI()
    

    def initUI(self):
        self.setProperty("elevation", "02dp")

        layout = QVBoxLayout()

        form_layout = QFormLayout()

        composition = QComboBox()
        composition.setEnabled(False)
        composition.addItems(list(CompositionMode.keys()))
        composition.currentTextChanged.connect(
            lambda text: LayerList.getInstance().selectedLayers()[0].setCompositionMode(
                CompositionMode.get(text, QPainter.CompositionMode_SourceOver)
            )
        )
        LayerList.getInstance().changedSelection.connect(
            lambda count: composition.setEnabled(count == 1) or (
                count == 1 and composition.setCurrentText(
                    list(CompositionMode.keys())[list(CompositionMode.values()).index(
                        LayerList.getInstance().selectedLayers()[0].compositionMode()
                    )]
                )
            )
        )
        form_layout.addRow("Composition", composition)

        opacity = QSlider(Qt.Horizontal)
        opacity.setMinimum(0)
        opacity.setMaximum(100)
        opacity.setSingleStep(1)
        opacity.setPageStep(10)
        opacity.setValue(100)
        opacity.setEnabled(False)
        opacity.valueChanged.connect(
            lambda value: LayerList.getInstance().selectedLayers()[0].setOpacity(value)
        )
        LayerList.getInstance().changedSelection.connect(
            lambda count: opacity.setEnabled(count == 1) or (
                count == 1 and opacity.setValue(
                    LayerList.getInstance().selectedLayers()[0].opacity())
            )
        )
        self._widgets["opacity"] = opacity
        form_layout.addRow("Opacity", opacity)
        layout.addLayout(form_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidget(LayerList.getInstance())
        scroll_area.setAlignment(Qt.AlignHCenter)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll_area.setProperty("elevation", self.property("elevation"))

        layout.addWidget(scroll_area)

        remove_layer = QPushButton()
        remove_layer.setObjectName("removeLayer")
        remove_layer.clicked.connect(
            lambda _: [
                LayerList.getInstance().removeLayer(layer)
                for layer in LayerList.getInstance().selectedLayers()
            ])
        self.setStyleSheet((
            " QPushButton#removeLayer { color: #ea2027; } "
            " QPushButton#removeLayer:disabled { color: #905e5f; } "
        ))
        self._widgets["remove_layer"] = remove_layer
        self._updateRemoveLayerButton()
        LayerList.getInstance().changedSelection.connect(
            lambda _: self._updateRemoveLayerButton())
        layout.addWidget(remove_layer)

        self.setLayout(layout)
    

    def _updateRemoveLayerButton(self):
        count = LayerList.getInstance().selectedLayersCount()

        self._widgets["remove_layer"].setEnabled(count > 0)
        self._widgets["remove_layer"].setText("Delete Layer" + ("s" if count > 1 else ""))
    

    @staticmethod
    def getInstance():
        if LayerPane.__instance == None:
            LayerPane()
        return LayerPane.__instance


class LayerList(QWidget):
    __instance = None

    layerAdded = pyqtSignal()
    layerRemoved = pyqtSignal()

    changedSelection = pyqtSignal(int)

    def __init__(self):
        if LayerList.__instance != None:
            raise Exception("Singleton")
        else:
            super().__init__()
            LayerList.__instance = self
        
        self._layers = []

        self._layer_names = {}

        self.initUI()
    

    def nextLayerName(self, name, dry_run = False):
        name = name.strip()
        if len(name) == 0:
            name = "Layer #{}".format(self.count())

        if name not in self._layer_names:
            self._layer_names[name] = 0
        
        self._layer_names[name] += 1

        new_name = name
        if self._layer_names[name] > 1:
            new_name = "{} ({})".format(name, self._layer_names[name] - 1)
        
        if dry_run:
            self._layer_names[name] = max(0, self._layer_names[name] - 1)
        
        return new_name
    

    def count(self):
        return len(self._layers)
    

    def selectedLayers(self):
        return [layer for layer in self._layers if layer.isLayerSelected()]
    
    def selectedLayersCount(self):
        return len(self.selectedLayers())
    

    def multiSelection(self):
        return self.selectedLayersCount() > 1
    

    def forEach(self, func):
        for layer in self._layers:
            func(layer)
    

    def layerAt(self, index):
        if index < 0 or index >= len(self._layers):
            return None
        return self._layers[index]
    

    def layerByName(self, name):
        for layer in self._layers:
            if layer.name() == name:
                return layer
        return None
    

    def index(self, layer):
        if not isinstance(layer, LayerItem) or layer not in self._layers:
            return -1

        return self._layers.index(layer)
    

    def moveLayer(self, layer, to_index):
        if (not isinstance(layer, LayerItem) or
            layer not in self._layers or
            to_index < 0 or to_index >= len(self._layers)
        ):
            return False
        
        from_index = self.index(layer)
        if from_index == to_index:
            return True
        
        self._layers.remove(layer)
        self.layout().removeWidget(layer)

        self._layers.insert(to_index, layer)
        self.layout().insertWidget(to_index, layer)

        lower = min(from_index, to_index)
        upper = max(from_index, to_index)
        for i in range(lower, upper + 1):
            self._layers[i].indexChanged.emit(i)

        return True


    def addLayer(self, layer):
        if layer is None or not isinstance(layer, LayerItem):
            return

        if layer not in self._layers:
            layer.clicked.connect(lambda e: self.changeSelection(layer, e))

            self._layers.insert(0, layer)
            self.layout().insertWidget(0, layer)

            self.layerAdded.emit()

            for i, l in enumerate(self._layers):
                l.indexChanged.emit(i)
    

    def removeLayer(self, layer):
        if layer in self._layers:
            name = re.sub(r"^(.*)\s\([0-9]+\)$", r"\1", layer.name())
            self._layer_names[name] = max(0, self._layer_names.get(name, 1) - 1)
     
            self._layers.remove(layer)
            self.layout().removeWidget(layer)

            self.layerRemoved.emit()
            if layer.isLayerSelected():
                self.changedSelection.emit(self.selectedLayersCount())

            layer.removed.emit(layer.name())

            layer.deleteLater()


    def changeSelection(self, layer, qevent):
        if layer is None or not isinstance(layer, LayerItem):
            return

        if qevent is None or qevent.modifiers() == Qt.NoModifier:
            # Replace selection
            if self.multiSelection():
                layer.setLayerSelected(True)
            else:
                layer.setLayerSelected(not layer.isLayerSelected())

            for l in self._layers:
                if l == layer:
                    continue
                l.setLayerSelected(False)
            
        elif qevent.modifiers() == Qt.ControlModifier:
            # Append to selection
            layer.setLayerSelected(not layer.isLayerSelected())

        elif qevent.modifiers() == Qt.ShiftModifier:
            # Select all in-between
            pass

        self.changedSelection.emit(self.selectedLayersCount())
    

    def initUI(self):
        self.setProperty("elevation", "02dp")

        layout = QVBoxLayout()
        layout.setSizeConstraint(QLayout.SetMinimumSize)
        layout.setSpacing(0)
        layout.addStretch()
        self.setLayout(layout)
    

    @staticmethod
    def getInstance():
        if LayerList.__instance == None:
            LayerList()
        return LayerList.__instance


class LayerItem(QWidget):

    visibilityChanged = pyqtSignal(bool)
    thumbnailChanged = pyqtSignal()
    nameChanged = pyqtSignal(str)
    selectionChanged = pyqtSignal(bool)
    indexChanged = pyqtSignal(int)

    opacityChanged = pyqtSignal(int)
    compositionModeChanged = pyqtSignal(int)

    clicked = pyqtSignal(QMouseEvent)
    removed = pyqtSignal(str)

    ThumbnailSize = 48

    def __init__(self):
        super().__init__()

        self._thumbnail = QPixmap(LayerItem.ThumbnailSize, LayerItem.ThumbnailSize)
        self._name = ""
        self._visible = True
        self._selected = False
        self._opacity = 100
        self._composition_mode = QPainter.CompositionMode_SourceOver

        self.setProperty("selected", False)
        self.setProperty("elevation", "08dp")

        self._widgets = {}

        self.setAutoFillBackground(True)

        self.initUI()
    

    def isLayerSelected(self):
        return self._selected

    def setLayerSelected(self, b):
        if self._selected != b:
            self._selected = b
            self.selectionChanged.emit(b)
            self.setProperty("selected", b)
            self.setPalette(
                QPalette(
                    QColor(7, 10, 20, 30) if b else QColor(0, 0, 0, 0)
                )
            )


    def isLayerVisible(self):
        return self._visible

    def setLayerVisible(self, b):
        self._visible = b
        self._widgets["hidden"].setCheckState(Qt.Unchecked if b else Qt.Checked)
        self.visibilityChanged.emit(b)
    

    def thumbnail(self):
        return self._thumbnail
    
    def setThumbnail(self, pixmap):
        self._thumbnail.fill(Qt.transparent)

        if pixmap is None or not isinstance(pixmap, QPixmap) or pixmap.width() == 0 or pixmap.height() == 0:
            return

        leading_dim = max(pixmap.width(), pixmap.height())

        painter = QPainter(self._thumbnail)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.scale(
            self._thumbnail.width() / leading_dim,
            self._thumbnail.height() / leading_dim)
        painter.translate(
            (leading_dim - pixmap.width()) * 0.5,
            (leading_dim - pixmap.height()) * 0.5)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()

        self._widgets["thumbnail"].setPixmap(self._thumbnail)
        self.thumbnailChanged.emit()
    

    def name(self):
        return self._name
    
    def setName(self, name):
        self._name = name
        self._widgets["name"].setText(self._name)
        self.nameChanged.emit(name)
    

    def opacity(self):
        return self._opacity
    
    def setOpacity(self, opacity):
        self._opacity = max(0, min(100, int(opacity)))
        self.opacityChanged.emit(self._opacity)
    

    def compositionMode(self):
        return self._composition_mode
    
    def setCompositionMode(self, composition):
        self._composition_mode = composition
        self.compositionModeChanged.emit(self._composition_mode)
    

    def initUI(self):
        layout = QHBoxLayout()

        hidden = check.IconCheckBox()
        hidden.setIcon(Qt.Unchecked, uLoader.icon("baseline_visibility_black_24dp.png"))
        hidden.setIcon(Qt.Checked, uLoader.icon("baseline_visibility_off_black_24dp.png"))
        hidden.stateChanged.connect(lambda s: self.setLayerVisible(s == Qt.Unchecked))
        layout.addWidget(hidden)
        self._widgets["hidden"] = hidden

        layout.addSpacing(5)

        thumbnail = QLabel()
        thumbnail.setPixmap(self.thumbnail())
        layout.addWidget(thumbnail)
        self._widgets["thumbnail"] = thumbnail

        layout.addSpacing(10)

        name = QLabel()
        name.setText(self.name())
        layout.addWidget(name)
        self._widgets["name"] = name

        layout.addStretch()

        vbox = QVBoxLayout()
        vbox.setSpacing(0)

        move_up = button.PixmapButton(uLoader.icon("baseline_expand_less_black_24dp.png").pixmap(20, 20))
        move_down = button.PixmapButton(uLoader.icon("baseline_expand_more_black_24dp.png").pixmap(20, 20))
        
        move_up.clicked.connect(lambda _:
            LayerList.getInstance().moveLayer(
                self, max(0, LayerList.getInstance().index(self) - 1)
            )
        )

        move_down.clicked.connect(lambda _:
            LayerList.getInstance().moveLayer(
                self, min(
                    LayerList.getInstance().count() - 1,
                    LayerList.getInstance().index(self) + 1
                )
            )
        )

        vbox.addStretch()
        vbox.addWidget(move_up)
        vbox.addWidget(move_down)
        vbox.addStretch()

        layout.addLayout(vbox)

        self.setLayout(layout)
    

    def mouseReleaseEvent(self, qevent: QMouseEvent):
        self.clicked.emit(qevent)
