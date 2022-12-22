from typing import List, Dict
from logging import getLogger

from pytissueoptics.scene.geometry import Environment
from pytissueoptics.scene.geometry import Polygon

logger = getLogger(__name__)


class SurfaceCollection:
    def __init__(self):
        self._surfaces: Dict[str, List[Polygon]] = {}

    @property
    def surfaceLabels(self) -> List[str]:
        return list(self._surfaces.keys())

    def add(self, surfaceLabel: str, polygons: List[Polygon]):
        if self._contains(surfaceLabel):
            logger.debug("A surface with the same label already exists. Incrementing label.")
            surfaceLabel = self._validateLabel(surfaceLabel)
        self._surfaces[surfaceLabel] = []
        self.setPolygons(surfaceLabel, polygons)

    def getPolygons(self, surfaceLabel: str = None) -> List[Polygon]:
        if surfaceLabel:
            self._assertContains(surfaceLabel)
            return self._surfaces[surfaceLabel]
        else:
            allPolygons = []
            for surfacePolygons in self._surfaces.values():
                allPolygons.extend(surfacePolygons)
            return allPolygons

    def setPolygons(self, surfaceLabel: str, polygons: List[Polygon]):
        self._assertContains(surfaceLabel)
        for polygon in polygons:
            polygon.surfaceLabel = surfaceLabel

        self._surfaces[surfaceLabel] = polygons

    def setOutsideEnvironment(self, environment: Environment, surfaceLabel: str = None):
        if surfaceLabel:
            outsidePolygons = self.getPolygons(surfaceLabel)
        else:
            outsidePolygons = []
            for surfaceLabel in self.surfaceLabels:
                if "interface" in surfaceLabel:
                    continue
                outsidePolygons.extend(self.getPolygons(surfaceLabel))

        for polygon in outsidePolygons:
            polygon.setOutsideEnvironment(environment)

    def getInsideEnvironment(self, surfaceLabel: str) -> Environment:
        polygons = self.getPolygons(surfaceLabel)
        environment = polygons[0].insideEnvironment
        for polygon in polygons:
            if polygon.insideEnvironment != environment:
                raise Exception("Surface insideMaterial is not constant. ")
        return environment

    def resetNormals(self):
        for polygon in self.getPolygons():
            polygon.resetNormal()

    def resetBoundingBoxes(self):
        for polygon in self.getPolygons():
            polygon.resetBoundingBox()

    def resetCentroids(self):
        for polygon in self.getPolygons():
            polygon.resetCentroid()

    def extend(self, other: 'SurfaceCollection'):
        assert not any(self._contains(surface) for surface in other.surfaceLabels)
        self._surfaces.update(other._surfaces)

    def _assertContains(self, surfaceLabel: str):
        assert self._contains(surfaceLabel), f"Surface labeled {surfaceLabel} not found in available surfaces: " \
                                             f"{self.surfaceLabels}. "

    def _contains(self, surfaceLabel: str) -> bool:
        return surfaceLabel in self.surfaceLabels

    def _validateLabel(self, surfaceLabel: str) -> str:
        if surfaceLabel not in self.surfaceLabels:
            return surfaceLabel
        idx = 0
        while f"{surfaceLabel}_{idx}" in self.surfaceLabels:
            idx += 1
        return f"{surfaceLabel}_{idx}"