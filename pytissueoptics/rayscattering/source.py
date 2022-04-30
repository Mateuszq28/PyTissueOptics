from typing import List, Optional

from pytissueoptics.rayscattering.tissues.rayScatteringScene import RayScatteringScene
from pytissueoptics.rayscattering.photon import Photon
from pytissueoptics.scene.solids import Sphere
from pytissueoptics.scene.geometry import Vector, Environment
from pytissueoptics.scene.intersection import SimpleIntersectionFinder
from pytissueoptics.scene.logger import Logger
from pytissueoptics.scene.viewer import MayaviViewer


class Source:
    def __init__(self, position: Vector, direction: Vector, photons: List[Photon]):
        self._position = position
        self._direction = direction
        self._direction.normalize()

        self._photons = photons
        self._environment = None

    def propagate(self, scene: RayScatteringScene, logger: Logger = None):
        intersectionFinder = SimpleIntersectionFinder(scene)
        self._environment = scene.getEnvironmentAt(self._position)
        self._prepareLogger(logger)

        for photon in self._photons:
            photon.setContext(self._environment, intersectionFinder=intersectionFinder, logger=logger)
            photon.propagate()

    def _prepareLogger(self, logger: Optional[Logger]):
        if logger is None:
            return
        if "photonCount" not in logger.info:
            logger.info["photonCount"] = 0
        logger.info["photonCount"] += self.getPhotonCount()

    @property
    def photons(self):
        return self._photons

    def getPhotonCount(self) -> int:
        return len(self._photons)

    def getPosition(self) -> Vector:
        return self._position

    def getEnvironment(self) -> Environment:
        if self._environment is None:
            return Environment(None)
        return self._environment

    def addToViewer(self, viewer: MayaviViewer, size: float = 0.1):
        sphere = Sphere(radius=size/2, position=self._position)
        viewer.add(sphere, representation="surface", colormap="Wistia", opacity=0.8)


class PencilSource(Source):
    def __init__(self, position=Vector(0, 0, 0), direction=Vector(0, 0, 1), N=100):
        photons = []
        for _ in range(N):
            photons.append(Photon(position=position.copy(), direction=direction.copy()))

        super().__init__(position, direction, photons)
