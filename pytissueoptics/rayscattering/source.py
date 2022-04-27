from typing import List

from pytissueoptics.rayscattering.tissues.rayScatteringScene import RayScatteringScene
from pytissueoptics.rayscattering.photon import Photon
from pytissueoptics.scene.geometry import Vector
from pytissueoptics.scene.intersection import SimpleIntersectionFinder
from pytissueoptics.scene.logger import Logger


class Source:
    def __init__(self, position: Vector, direction: Vector, photons: List[Photon]):
        self._position = position
        self._direction = direction
        self._direction.normalize()

        self._photons = photons

    def propagate(self, scene: RayScatteringScene, logger: Logger = None):
        intersectionFinder = SimpleIntersectionFinder(scene)
        sourceEnvironment = scene.getEnvironmentAt(self._position)
        for photon in self._photons:
            photon.setContext(sourceEnvironment, intersectionFinder=intersectionFinder, logger=logger)
            photon.propagate()

    @property
    def photons(self):
        return self._photons

    def getPhotonCount(self) -> int:
        return len(self._photons)


class PencilSource(Source):
    def __init__(self, position=Vector(0, 0, 0), direction=Vector(0, 0, 1), N=100):
        photons = []
        for _ in range(N):
            photons.append(Photon(position=position.copy(), direction=direction.copy()))

        super().__init__(position, direction, photons)
