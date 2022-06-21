from PyQt5.QtCore import QObject, QPointF

import src.backend.layers as beLayers
import src.ui.sidebar.layers as sbLayers
import src.ui.canvas.layers as cvLayers

import src.ui.canvas.canvas as canvas

class LayerManager(QObject):
    __instance = None

    def __init__(self):
        if LayerManager.__instance != None:
            raise Exception("Singleton")
        else:
            super().__init__()
            LayerManager.__instance = self
        
        self._items = {}
        self._count = 0
    

    def allLayers(self):
        return list(self._items.values())
    

    def getLayer(self, layer, out_type):
        if (out_type is None
            or layer is None
        ):
            return None

        in_index = -1
        if isinstance(layer, beLayers.Layer):
            in_index = 0
        elif isinstance(layer, sbLayers.LayerItem):
            in_index = 1
        elif isinstance(layer, cvLayers.PixmapLayer):
            in_index = 2
        else:
            return None
        
        out_index = -1
        if out_type is beLayers.Layer:
            out_index = 0
        elif out_type is sbLayers.LayerItem:
            out_index = 1
        elif out_type is cvLayers.PixmapLayer:
            out_index = 2
        else:
            return None
        
        for item_key in self._items:
            if self._items[item_key][in_index] == layer:
                return self._items[item_key][out_index]
        
        return None
    

    def addItem(self, file_path: str, pixels, name = "", initial_offset = QPointF(0, 0)):
        be_layer = beLayers.Layer()
        be_layer.setImageData(file_path, pixels)

        sb_layer = sbLayers.LayerItem()
        sb_layer.setName(
            sbLayers.LayerList.getInstance().nextLayerName(name))
        
        cv_layer = cvLayers.PixmapLayer()
        cv_layer.linkBackendLayer(be_layer)
        cv_layer.linkSideBarLayer(sb_layer)
        cv_layer.setPosition(cv_layer.position() + initial_offset)

        self._items[self._count] = (be_layer, sb_layer, cv_layer)
        sb_layer.removed.connect(self._removeItem(self._count))
        self._count += 1

        sbLayers.LayerList.getInstance().addLayer(sb_layer)
        canvas.Canvas.getInstance().getView("main").addItem(cv_layer)

        return self._items[self._count - 1]
    

    def _removeItem(self, index):
        def anon():
            if index not in self._items:
                return

            item = self._items[index]
            if (item is None
                or len(item) != 3
                or not isinstance(item[0], beLayers.Layer)
                or not isinstance(item[1], sbLayers.LayerItem)
                or not isinstance(item[2], cvLayers.PixmapLayer)
            ):
                print("[Warning] Can not remove invalid item")
                return
            
            be_layer = item[0]
            sb_layer = item[1]
            cv_layer = item[2]

            del self._items[index]

            canvas.Canvas.getInstance().getView("main").removeItem(cv_layer)
            sbLayers.LayerList.getInstance().removeLayer(sb_layer)

            cv_layer.unlinkSideBarLayer
            cv_layer.unlinkBackendLayer()

            be_layer.endThread()

            del cv_layer
            del sb_layer
            del be_layer
        
        return anon


    @staticmethod
    def getInstance():
        if LayerManager.__instance == None:
            LayerManager()
        return LayerManager.__instance
