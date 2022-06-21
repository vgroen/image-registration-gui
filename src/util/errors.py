from PyQt5.QtWidgets import QErrorMessage

import src.ui.window as window

class ErrorCode:
    Ok = 0

    Solver_InvalidGroup = 1
    Solver_IncorrectParameterAmount = 2
    Solver_NoReference = 3
    Solver_NoTemplates = 4

    Align_BusyGroup = 5

    Manager_NoGroup = 6

    Export_NoLayers = 7


    __messages = {
        Ok: "",

        Solver_InvalidGroup: "",
        Solver_IncorrectParameterAmount: "",
        Solver_NoReference: "The selected group does not have a valid reference layer",
        Solver_NoTemplates: "The selected group does not have a valid template layer",

        Align_BusyGroup: "The selected group is already being aligned",

        Manager_NoGroup: "",

        Export_NoLayers: "Nothing to export, there are no layers"
    }

    @staticmethod
    def showDialog(code, *args):
        if (code not in ErrorCode.__messages
            or len(ErrorCode.__messages[code]) == 0
        ):
            return

        dialog = QErrorMessage(window.Window.getInstance())
        dialog.showMessage(ErrorCode.__messages[code].format(*args))
