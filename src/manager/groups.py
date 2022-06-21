from PyQt5.QtCore import QObject

import src.backend.groups as beGroups
import src.ui.sidebar.groups as sbGroups

import src.backend.layers as beLayers
import src.ui.sidebar.layers as sbLayers

import src.manager.layers as mgLayers

class GroupManager(QObject):
    __instance = None

    def __init__(self):
        if GroupManager.__instance != None:
            raise Exception("Singleton")
        else:
            super().__init__()
            GroupManager.__instance = self
        
        self._items = {}
        self._count = 0
    

    def allGroups(self):
        return list(self._items.values())
    

    def activeGroup(self, out_type):
        return self.getGroup(
            sbGroups.GroupPane.getInstance().activeGroup(),
            out_type
        )


    def getGroup(self, group, out_type):
        if (out_type is None
            or group is None
        ):
            return None
        
        in_index = -1
        if isinstance(group, beGroups.Group):
            in_index = 0
        elif isinstance(group, sbGroups.GroupItem):
            in_index = 1
        else:
            return None
        
        out_index = -1
        if out_type is beGroups.Group:
            out_index = 0
        elif out_type is sbGroups.GroupItem:
            out_index = 1
        else:
            return None
        
        for item_key in self._items:
            if self._items[item_key][in_index] == group:
                return self._items[item_key][out_index]
        
        return None



    def addItem(self):
        be_group = beGroups.Group()

        sb_group = sbGroups.GroupItem()

        name_to_belayer = (lambda name:
            mgLayers.LayerManager.getInstance().getLayer(
                layer=sbLayers.LayerList.getInstance().layerByName(name),
                out_type=beLayers.Layer
            )
        )

        sb_group.referenceChanged.connect(
            lambda name: be_group.setReferenceLayer(name_to_belayer(name)))
        sb_group.templateAdded.connect(
            lambda name: be_group.addTemplateLayer(name_to_belayer(name)))
        sb_group.templateRemoved.connect(
            lambda name: be_group.removeTemplateLayer(name_to_belayer(name)))

        self._items[self._count] = (be_group, sb_group)
        sb_group.removed.connect(self._removeItem(self._count))
        self._count += 1

        sbGroups.GroupPane.getInstance().addGroup(sb_group)

        if sb_group.referenceLayer() is not None:
            be_group.setReferenceLayer(name_to_belayer(sb_group.referenceLayer().name()))
        for template in sb_group.templateLayers():
            be_group.addTemplateLayer(name_to_belayer(template.name()))
    

    def _removeItem(self, index):
        def anon():
            if index not in self._items:
                return
            
            item = self._items[index]
            if (item is None
                or len(item) != 2
                or not isinstance(item[0], beGroups.Group)
                or not isinstance(item[1], sbGroups.GroupItem)
            ):
                print("[Warning] Can not remove invalid item")
                return
            
            be_group = item[0]
            sb_group = item[1]

            del self._items[index]

            sbGroups.GroupPane.getInstance().removeGroup(sb_group)

            del sb_group
            del be_group
        
        return anon


    @staticmethod
    def getInstance():
        if GroupManager.__instance == None:
            GroupManager()
        return GroupManager.__instance
