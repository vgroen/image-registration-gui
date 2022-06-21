from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QColor

import src.manager.layers as mgLayers
import src.manager.groups as mgGroups
import src.backend.groups as beGroups
import src.backend.solver as beSolver
import src.ui.sidebar.groups as sbGroups
import src.ui.sidebar.layers as sbLayers
import src.ui.canvas.layers as cvLayers
import src.ui.canvas.matches as cvMatches
import src.ui.canvas.canvas as canvas
import src.util.threads as threads
from src.util.errors import ErrorCode

Colors = [
    QColor(231, 76, 60),
    QColor(230, 126, 34),
    QColor(241, 196, 15),
    QColor(46, 204, 113),
    QColor(26, 188, 156),
    QColor(52, 152, 219),
    QColor(155, 89, 182)
]

def createSolverFromGroup(be_group):
    if (be_group is None
        or not isinstance(be_group, beGroups.Group)
    ):
        return ErrorCode.Solver_InvalidGroup

    solver = beSolver.Solver()
    status = solver.setGroup(be_group)

    if status == ErrorCode.Solver_InvalidGroup:
        return status

    sb_group = mgGroups.GroupManager.getInstance().getGroup(be_group, sbGroups.GroupItem)

    if sb_group is None:
        return ErrorCode.Manager_NoGroup

    if sb_group.isProcessing():
        ErrorCode.showDialog(ErrorCode.Align_BusyGroup)
        return ErrorCode.Align_BusyGroup


    def done_with_conover(id):
        def done_with_deformation(*args):
            sb_group.setFitness(result["fitness"])
            sb_group.setIsProcessing(False)
            return

        result = solver.result(id)

        if result == None or result["fitness"] == -1:
            sb_group.setFitness(-1)
            sb_group.setIsProcessing(False)
            return

        be_layer = result["template"]
        be_layer.setFullResolutionInterpolated(result["aligned_template"])
        job = threads.ThreadPool.getInstance().submit(
            be_layer.setInterpolationCoefficients,
            result["xoptimal"], result["yoptimal"]
        )
        job.add_done_callback(done_with_deformation)

        index = sbGroups.GroupPane.getInstance().indexOf(sb_group)

        if index != -1:
            matches = cvMatches.MatchesLayer()
            matches.linkSideBarGroup(sb_group)
            matches.linkSideBarLayer(
                mgLayers.LayerManager.getInstance().getLayer(
                    be_layer, sbLayers.LayerItem
                )
            )

            pen = matches.pen()
            pen.setColor(Colors[index % len(Colors)])
            matches.setPen(pen)

            offset = QPointF(result["transform"][0, 2], result["transform"][1, 2])

            for i in range(len(result["keypoints_reference"])):
                matches.addMatch(
                    QPointF(*(result["keypoints_reference"][i])) + offset,
                    QPointF(*(result["keypoints_template"][i]))
                )
            
            cv_layer = mgLayers.LayerManager.getInstance().getLayer(
                be_layer, cvLayers.PixmapLayer
            )
            cv_layer.setPosition(offset)

            canvas.Canvas.getInstance().getView("main").addItem(matches)
            matches.setVisible(True)

        return

    solver.finishedLayer.connect(done_with_conover)

    status = solver.start()

    if status != ErrorCode.Ok:
        ErrorCode.showDialog(status)
        return status

    sb_group.setIsProcessing(True)
