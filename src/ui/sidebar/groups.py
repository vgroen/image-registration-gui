from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import src.ui.sidebar.layers as sbLayers
import src.manager.groups as mgGroups
import src.backend.groups as beGroups
import src.util.align as uAlign

from src.external.qtwaitingspinner.waitingspinnerwidget import QtWaitingSpinner

class GroupPane(QGroupBox):
    __instance = None

    def __init__(self):
        if GroupPane.__instance != None:
            raise Exception("Singleton")
        else:
            super().__init__("Groups")
            GroupPane.__instance = self
        
        self._tab_count = 0

        self._widgets = {}
        self.initUI()
    

    def indexOf(self, group):
        return self._widgets["tabs"].indexOf(group)

    def activeGroup(self):
        return self._widgets["tabs"].currentWidget()
    

    def addGroup(self, group):
        index = self._widgets["tabs"].count() - 1

        group.setName("Group {}".format(self._tab_count))
        group.removed.connect(lambda: self.removeGroup(group))

        self._widgets["tabs"].insertTab(
            index, group, group.name())
        
        self._widgets["tabs"].setCurrentIndex(index)
        self._tab_count += 1
    

    def removeGroup(self, group):
        index = self._widgets["tabs"].indexOf(group)
        if index == -1 or index == self._widgets["tabs"].count() - 1:
            return
        
        next_index = max(0, index - 1)
        self._widgets["tabs"].setCurrentIndex(next_index)
        self._widgets["tabs"].removeTab(index)

        if self._widgets["tabs"].count() == 1:
            mgGroups.GroupManager.getInstance().addItem()
    

    def initUI(self):
        self.setProperty("elevation", "02dp")

        layout = QVBoxLayout()

        tabs = QTabWidget(None)
        lasttab = QLabel("Add a new group with the + button")
        lasttab.setAlignment(Qt.AlignCenter)
        tabs.addTab(lasttab, "+")

        tabs.currentChanged.connect(self.tabChangeEvent)
        layout.addWidget(tabs)
        self._widgets["tabs"] = tabs

        mgGroups.GroupManager.getInstance().addItem()

        self.setLayout(layout)
    

    def tabChangeEvent(self, index):
        # Adapted from:
        # https://newbedev.com/how-can-i-add-a-new-tab-button-next-to-the-tabs-of-a-qmdiarea-in-tabbed-view-mode
        if index == self._widgets["tabs"].count() - 1:
            mgGroups.GroupManager.getInstance().addItem()
        
        for i in range(self._widgets["tabs"].count() - 1):
            self._widgets["tabs"].widget(i).setShowMatches(i == index)
        

    @staticmethod
    def getInstance():
        if GroupPane.__instance == None:
            GroupPane()
        return GroupPane.__instance


class GroupItem(QWidget):
    nameChanged = pyqtSignal(str)
    referenceChanged = pyqtSignal(str)
    templateAdded = pyqtSignal(str)
    templateRemoved = pyqtSignal(str)
    removed = pyqtSignal()
    processStatusChanged = pyqtSignal(bool)

    showMatchesChanged = pyqtSignal(bool)

    def __init__(self):
        super().__init__()

        self._name = ""

        self._reference_layer = None
        self._template_layers = []

        self._is_processing = False
        self._show_matches = False

        self._widgets = {}
        self.initUI()
        self._connectAll()
    

    def _connectAll(self):
        sbLayers.LayerList.getInstance().layerAdded.connect(self._updateReferenceBox)
        sbLayers.LayerList.getInstance().layerRemoved.connect(self._updateReferenceBox)

        sbLayers.LayerList.getInstance().layerAdded.connect(self._updateTemplateBox)
        sbLayers.LayerList.getInstance().layerRemoved.connect(self._updateTemplateBox)

        self.referenceChanged.connect(self._updateTemplateBox)
        self.processStatusChanged.connect(self._widgets["remove_group"].setDisabled)
        self.processStatusChanged.connect(self._widgets["align_group"].setDisabled)
        self.processStatusChanged.connect(self._widgets["ref_box"].setDisabled)
        self.processStatusChanged.connect(self._widgets["show_matches"].setDisabled)
        self.processStatusChanged.connect(self._updateTemplateBox)

        self._widgets["remove_group"].clicked.connect(self.remove)
        self._widgets["align_group"].clicked.connect(
            lambda _: uAlign.createSolverFromGroup(
                mgGroups.GroupManager.getInstance().getGroup(
                    self, beGroups.Group
                )
            )
        )


    def _disconnectAll(self):
        sbLayers.LayerList.getInstance().layerAdded.disconnect(self._updateReferenceBox)
        sbLayers.LayerList.getInstance().layerRemoved.disconnect(self._updateReferenceBox)

        sbLayers.LayerList.getInstance().layerAdded.disconnect(self._updateTemplateBox)
        sbLayers.LayerList.getInstance().layerRemoved.disconnect(self._updateTemplateBox)

        self.referenceChanged.disconnect(self._updateTemplateBox)

        self._widgets["remove_group"].clicked.disconnect(self.remove)
    

    def showMatches(self):
        return self._show_matches
    
    def setShowMatches(self, b):
        if self._show_matches != b:
            self._show_matches = b
            self.showMatchesChanged.emit(b)
    

    def setFitness(self, value):
        if value == -1:
            self._widgets["fitness"].setText("Failed")
        else:
            self._widgets["fitness"].setText("{:.4f}".format(value))


    def name(self):
        return self._name

    def setName(self, name):
        self._name = name
        self.nameChanged.emit(name)

    
    def referenceLayer(self):
        if self._reference_layer is None:
            return None

        layer = sbLayers.LayerList.getInstance().layerByName(self._reference_layer)
        if layer is None:
            self.setReferenceLayer(None)

        return layer


    def isProcessing(self):
        return self._is_processing

    def setIsProcessing(self, b):
        if self._is_processing != b:
            self._is_processing = b
            self.processStatusChanged.emit(b)
            self.showMatchesChanged.emit(not b)
    

    def setReferenceLayer(self, layer):
        if layer is not None and self._reference_layer != layer.name():
            self._reference_layer = layer.name()
            self.referenceChanged.emit(layer.name())
        elif layer is None:
            self._reference_layer = None
            self.referenceChanged.emit(None)

    
    def templateLayers(self):
        retval = []

        for template in self._template_layers.copy():
            layer = sbLayers.LayerList.getInstance().layerByName(template)
            if layer is None or template == self._reference_layer:
                self.setTemplateLayer(layer, False)
                continue
            
            retval.append(layer)
        
        return retval
    

    def setTemplateLayer(self, layer, b):
        if layer is None or not isinstance(layer, sbLayers.LayerItem):
            return
        
        name = layer.name()
        if b and not name in self._template_layers:
            layer.removed.connect(self.__templateRemovedSlot)
            self._template_layers.append(name)
            self.templateAdded.emit(name)
        
        if not b and name in self._template_layers:
            layer.removed.disconnect(self.__templateRemovedSlot)
            self._template_layers.remove(name)
            self.templateRemoved.emit(name)
    

    def remove(self):
        self._disconnectAll()
        self.removed.emit()
    

    def _setReferenceByName(self, name):
        self.setReferenceLayer(
            sbLayers.LayerList.getInstance().layerByName(name))

    def _updateReferenceBox(self):
        self._widgets["ref_box"].currentTextChanged.disconnect(
            self._setReferenceByName)
        self._widgets["ref_box"].clear()

        if sbLayers.LayerList.getInstance().count() > 0:
            sbLayers.LayerList.getInstance().forEach(
                lambda l: self._widgets["ref_box"].addItem(l.name()))
            
            selected_layer = self.referenceLayer()

            index = sbLayers.LayerList.getInstance().count() - 1
            for i in reversed(range(sbLayers.LayerList.getInstance().count())):
                if sbLayers.LayerList.getInstance().layerAt(i) not in self.templateLayers():
                    index = i
                    break

            if selected_layer is not None:
                index = sbLayers.LayerList.getInstance().index(selected_layer)
            else:
                self.setReferenceLayer(
                    sbLayers.LayerList.getInstance().layerAt(index))

            self._widgets["ref_box"].setCurrentIndex(index)

        self._widgets["ref_box"].currentTextChanged.connect(
            self._setReferenceByName)
                

    def _updateTemplateBox(self):
        layout = self._widgets["temp_box"].layout()
        while layout.count() > 0:
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        

        if self.isProcessing():
            label = QLabel("Calculating group alignment...")
            label.setAlignment(Qt.AlignHCenter)
            layout.addWidget(label)

            # Spinner made by Luca Weiss
            # https://github.com/z3ntu/QtWaitingSpinner
            spinner = QtWaitingSpinner(self)
            spinner.setRoundness(60)
            spinner.setNumberOfLines(12)
            spinner.setLineLength(9)
            spinner.setLineWidth(3)
            spinner.setRevolutionsPerSecond(1)
            spinner.start()

            layout.addWidget(spinner)

            return

        
        if sbLayers.LayerList.getInstance().count() == 0:
            return

        sbLayers.LayerList.getInstance().forEach(
            lambda l: layout.addWidget(QCheckBox(l.name())))

        layout.addStretch()

        sbLayers.LayerList.getInstance().forEach(
            lambda l: (
                layout
                    .itemAt(sbLayers.LayerList.getInstance().index(l))
                    .widget()
                    .stateChanged
                    .connect(
                        lambda state: self.setTemplateLayer(l, state == Qt.Checked)
                    )
            )
        )

        reference_layer = self.referenceLayer()
        if reference_layer is not None:
            index = sbLayers.LayerList.getInstance().index(reference_layer)
            layout.itemAt(index).widget().setEnabled(False)


        for template in self.templateLayers():
            index = sbLayers.LayerList.getInstance().index(template)
            if index == -1:
                continue
            layout.itemAt(index).widget().setCheckState(Qt.Checked)

        return


    def initUI(self):
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        fitness = QLabel()
        fitness.setText("No alignment")
        form_layout.addRow("Fitness", fitness)
        self._widgets["fitness"] = fitness

        matches_checkbox = QCheckBox()
        matches_checkbox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        matches_checkbox.stateChanged.connect(
            lambda state: self.showMatchesChanged.emit(state == Qt.Checked))
        matches_checkbox.setCheckState(Qt.Checked)
        form_layout.addRow("Visualise matches", matches_checkbox)
        self._widgets["show_matches"] = matches_checkbox

        # Reference box
        ref_box = QComboBox()
        self._widgets["ref_box"] = ref_box
        self._widgets["ref_box"].currentTextChanged.connect(
            self._setReferenceByName)
        self._updateReferenceBox()

        form_layout.addRow("Reference", ref_box)
        layout.addLayout(form_layout)

        # Templates box
        scroll_area = QScrollArea()
        scroll_area.setAlignment(Qt.AlignHCenter)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        temp_box = QWidget()
        temp_box.setLayout(QVBoxLayout())
        temp_box.layout().setSizeConstraint(QLayout.SetMinimumSize)
        temp_box.layout().setSpacing(0)

        scroll_area.setWidget(temp_box)
        self._widgets["temp_box"] = temp_box
        self._updateTemplateBox()

        layout.addWidget(QLabel("Template layers"))
        layout.addWidget(scroll_area)

        hbox = QHBoxLayout()

        align_group = QPushButton("Align Group")
        remove_group = QPushButton("Delete Group")

        align_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        remove_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        align_policy.setHorizontalStretch(3)
        remove_policy.setHorizontalStretch(2)

        align_group.setSizePolicy(align_policy)
        remove_group.setSizePolicy(remove_policy)

        remove_group.setObjectName("removeGroup")
        self.setStyleSheet((
            " QPushButton#removeGroup { color: #ea2027; } "
            " QPushButton#removeGroup:disabled { color: #905e5f; } "
        ))

        self._widgets["align_group"] = align_group
        self._widgets["remove_group"] = remove_group

        hbox.addWidget(align_group)
        hbox.addWidget(remove_group)

        layout.addLayout(hbox)

        self.setLayout(layout)


    def __templateRemovedSlot(self, name):
        self.templateRemoved.emit(name)
