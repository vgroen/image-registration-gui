from concurrent import futures
from PyQt5.QtCore import QObject, pyqtSignal

from src.util.errors import ErrorCode
import src.util.threads as threads

import src.backend.groups as beGroups
import src.backend.conover as conover

import random
import heapq

import numpy as np

class ConoverParams:
    Order = 0
    WindowSize = 1
    SearchRegionSize = 2
    ControlPointRegionSize = 3
    ScaleFactor = 4


class Solver(QObject):
    DefaultParameters = {
        ConoverParams.Order: 3,
        ConoverParams.WindowSize: 10,
        ConoverParams.SearchRegionSize: 20,
        ConoverParams.ControlPointRegionSize: 10,
        ConoverParams.ScaleFactor: 1
    }

    finishedLayer = pyqtSignal(int)


    def __init__(self):
        super().__init__()

        self._group = None
        self._inital_parameters = []

        self._results = []
    

    def result(self, id):
        if id < 0 or id >= len(self._results):
            return None
        return self._results[id]


    def group(self):
        return self._group
    
    def setGroup(self, group):
        if group is not None and not isinstance(group, beGroups.Group):
            return ErrorCode.Solver_InvalidGroup

        self._group = group
        self.setInitialParameters([
            Solver.DefaultParameters.copy()
            for _ in self.group().templateLayers()
        ])

        return ErrorCode.Ok
    

    def setInitialParameters(self, parameters):
        if self.group() is not None and len(parameters) != len(self.group().templateLayers()):
            return
        self._inital_parameters = parameters
    

    def start(self):
        if self.group() is None:
            print("[Warning] No valid group is selected")
            return ErrorCode.Solver_InvalidGroup
        
        if len(self._inital_parameters) != len(self.group().templateLayers()):
            print("[Warning] Solver requires {} parameters, got {}".format(
                len(self.group().templateLayers()),
                len(self._inital_parameters)
            ))
            return ErrorCode.Solver_IncorrectParameterAmount
        
        if self.group().referenceLayer() is None:
            print("[Warning] No reference layer selected")
            return ErrorCode.Solver_NoReference
        
        if len(self.group().templateLayers()) == 0:
            print("[Warning] No template layers selected")
            return ErrorCode.Solver_NoTemplates

        for i, template in enumerate(self.group().templateLayers()):
            job = threads.ThreadPool.getInstance().submit(
                self._optimize,
                template=template,
                parameters=self._inital_parameters[i].copy()
            )

            job.add_done_callback(self._emitResults)
        
        return ErrorCode.Ok
        
    
    def _emitResults(self, future):
        try:
            result = future.result(5)
            self._results.append(result)

            self.finishedLayer.emit(len(self._results) - 1)
        except futures.TimeoutError:
            return
    

    def _optimize(self, template, parameters = {}):
        parameters = Solver.DefaultParameters | parameters

        store = []
        minheap = []

        for i in range(15):
            params = Solver.mutateParameters(
                parameters if len(minheap) == 0 else store[minheap[0][-1]][1],
                exclude=[
                    ConoverParams.SearchRegionSize,
                    ConoverParams.ControlPointRegionSize,
                    ConoverParams.ScaleFactor
                ]
            )

            wavelet = conover.compute_modulus(
                template.fullResolutionMasked().sum(2),
                params[ConoverParams.Order]
            )

            control_points = conover.identify_control_points(
                wavelet,
                params[ConoverParams.WindowSize]
            )

            if len(control_points) == 0:
                continue

            score = -len(control_points)
            print(score)

            store.append((control_points, params))

            heapq.heappush(minheap, (
                score,
                -len(control_points),
                i,
                len(store) - 1 # Save the store index
            ))


        if len(minheap) == 0:
            return None
        

        store_index = minheap[0][-1]
        control_points, base_params = store[store_index]
        
        print(len(control_points))

        reference = self.group().referenceLayer()

        transform = conover.approximate_transformation(
            reference.fullResolutionPixels(),
            template.fullResolutionPixels(),
            255 - np.clip(template.fullResolutionMask()[:,:,3] * 255, 0, 255).astype(np.uint8)
        )

        n = 0
        max_n = 15
        best_result = {
            "fitness": -1,
            "point_count": 0
        }
        best_params = base_params

        best_params[ConoverParams.ControlPointRegionSize] = int(max(6, min(10, min(template.width(), template.height()) * 0.15)))
        best_params[ConoverParams.SearchRegionSize] = best_params[ConoverParams.ControlPointRegionSize] * 2

        while (n < max_n
            and (best_result["fitness"] == -1 or best_result["fitness"] > 1 / 6)
        ):
            n += 1
            print("{}/{}".format(n, max_n))

            params = Solver.mutateParameters(best_params, exclude=[
                ConoverParams.Order,
                ConoverParams.WindowSize
            ])

            result = conover.conover(
                reference.fullResolutionPixels().astype(np.float32),
                template.fullResolutionMasked().astype(np.float32),
                mask=template.fullResolutionMask()[:,:,3],
                order=params[ConoverParams.Order],
                windowsize=params[ConoverParams.WindowSize],
                search_region_size=params[ConoverParams.SearchRegionSize],
                control_point_region_size=params[ConoverParams.ControlPointRegionSize],
                scale_factor=params[ConoverParams.ScaleFactor],
                control_points=control_points,
                transform=transform
            )

            if (
                best_result is None
                or best_result["fitness"] == -1
                or (
                    result["fitness"] != -1
                    and (
                        result["fitness"] < best_result["fitness"]
                        or (
                            result["fitness"] == best_result["fitness"]
                            and result["point_count"] > best_result["point_count"]
                        )
                    )
                )
            ):
                best_result = result
                best_params = params

        print(best_params)
        return {
            "template": template,
            "parameters": best_params,
            **best_result
        }
    

    @staticmethod
    def mutateParameters(params, exclude = []):
        params = params.copy()

        if ConoverParams.Order not in exclude:
            params[ConoverParams.Order] = max(
                3, params[ConoverParams.Order] + random.randint(-2, 2))

        if ConoverParams.WindowSize not in exclude:
            params[ConoverParams.WindowSize] = max(
                5, params[ConoverParams.WindowSize] + random.randint(-4, 4))

        if ConoverParams.SearchRegionSize not in exclude:
            params[ConoverParams.SearchRegionSize] = max(
                params[ConoverParams.WindowSize],
                params[ConoverParams.SearchRegionSize] + random.randint(-4, 4))

        if ConoverParams.ControlPointRegionSize not in exclude:
            params[ConoverParams.ControlPointRegionSize] = max(
                params[ConoverParams.WindowSize],
                min(
                    params[ConoverParams.SearchRegionSize] - 1,
                    params[ConoverParams.ControlPointRegionSize] + random.randint(-4, 4)
                    )
                )

        if ConoverParams.ScaleFactor not in exclude:
            params[ConoverParams.ScaleFactor] = 1
        
        return params
