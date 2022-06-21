from PyQt5.QtCore import QObject

class MaskBrush(QObject):
    __instance = None

    def __init__(self):
        if MaskBrush.__instance != None:
            raise Exception("Singleton")
        else:
            super().__init__()
            MaskBrush.__instance = self
        
        self._radius = 35
        self._color_none = [ 0, 0, 0, 0 ]
        self._color_red = [ 0.95, 0.15, 0.30, 0.90 ]
    

    def radius(self):
        return self._radius
    
    def setRadius(self, radius):
        self._radius = radius
    

    def colorNone(self):
        return self._color_none
    
    def colorRed(self):
        return self._color_red


    @staticmethod
    def getInstance():
        if MaskBrush.__instance == None:
            MaskBrush()
        return MaskBrush.__instance