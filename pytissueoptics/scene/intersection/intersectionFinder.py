import sys
from dataclasses import dataclass
from typing import List, Union, Tuple, Optional

from pytissueoptics.scene.geometry import Vector, Polygon, Triangle, Quad
from pytissueoptics.scene.intersection import Ray
from pytissueoptics.scene.tree import SpacePartition, Node
from pytissueoptics.scene.intersection.bboxIntersect import GemsBoxIntersect
from pytissueoptics.scene.intersection.quadIntersect import MollerTrumboreQuadIntersect
from pytissueoptics.scene.intersection.triangleIntersect import MollerTrumboreTriangleIntersect
from pytissueoptics.scene.solids import Solid


@dataclass
class Intersection:
    distance: float
    position: Vector
    polygon: Polygon


class IntersectionFinder:
    def __init__(self, solids: List[Solid]):
        self._solids = solids
        self._triangleIntersect = MollerTrumboreTriangleIntersect()
        self._quadIntersect = MollerTrumboreQuadIntersect()
        self._boxIntersect = GemsBoxIntersect()

    def findIntersection(self, ray: Ray) -> Optional[Intersection]:
        raise NotImplementedError


class SimpleIntersectionFinder(IntersectionFinder):
    def findIntersection(self, ray: Ray) -> Optional[Intersection]:
        bboxIntersections = self._findBBoxIntersectingSolids(ray)
        bboxIntersections.sort(key=lambda x: x[0])
        for (distance, solid) in bboxIntersections:
            intersection = self._findClosestPolygonIntersection(ray, solid.getPolygons())
            if intersection:
                return intersection
        return None

    def _findBBoxIntersectingSolids(self, ray) -> Optional[List[Tuple[float, Solid]]]:
        """ We need to handle the special case where ray starts inside bbox. The Box Intersect will not compute
        the intersection for this case and will instead return ray.origin. When that happens, distance will be 0
        and we exit to check the polygons of this solid. """
        solidCandidates = []
        for solid in self._solids:
            bboxIntersection = self._boxIntersect.getIntersection(ray, solid.bbox)
            if not bboxIntersection:
                continue
            distance = (bboxIntersection - ray.origin).getNorm()
            solidCandidates.append((distance, solid))
            if distance == 0:
                break
        return solidCandidates

    def _findClosestPolygonIntersection(self, ray: Ray, polygons: List[Polygon]) -> Optional[Intersection]:
        closestPolygon = None
        closestIntersection = None
        closestDistance = sys.maxsize
        for polygon in polygons:
            intersection = self._findPolygonIntersection(ray, polygon)
            if not intersection:
                continue
            distance = (intersection - ray.origin).getNorm()
            if distance < closestDistance:
                closestDistance = distance
                closestIntersection = intersection
                closestPolygon = polygon
        if not closestIntersection:
            return None
        return Intersection(closestDistance, closestIntersection, closestPolygon)

    def _findPolygonIntersection(self, ray: Ray, polygon: Polygon) -> Optional[Vector]:
        if isinstance(polygon, Triangle):
            return self._triangleIntersect.getIntersection(ray, polygon)
        if isinstance(polygon, Quad):
            return self._quadIntersect.getIntersection(ray, polygon)


class FastIntersectionFinder(IntersectionFinder):
    def __init__(self, solids: List[Solid], partition: SpacePartition):
        super(FastIntersectionFinder, self).__init__(solids)
        self._partition = partition

    def findIntersection(self, ray: Ray) -> Optional[Intersection]:
        """
        This algorithm is a simple home-made algorithm. It starts by locating the starting point of the ray inside
        the SpacePartition. Once we have a node, we can verify if the ray intersects its children bounding boxes.
        If it does, we'll repeat this process until we find the leaf node that the ray touches.

        Limitations:    - does not take in consideration if the touched polygon is shared amongst many nodes
        """
        rayStartingNode = self._partition.searchPoint(ray.origin)
        if rayStartingNode is None:
            rayStartingNode = self._partition.root
        intersection = self._findIntersection(ray, rayStartingNode)
        if intersection:
            return intersection
        return None

    def _findIntersection(self, ray: Ray, node: Node = None) -> Optional[Intersection]:
        if not node.isLeaf:
            closestIntersection = None
            for child in node.children:
                if not child.visited:
                    bboxIntersection = self._boxIntersect.getIntersection(ray, child.bbox)
                    child.visited = True

                    if bboxIntersection is not None:
                        intersection = self._findIntersection(ray, child)

                        if intersection is not None:

                            if closestIntersection is None:
                                closestIntersection = intersection

                            elif intersection.distance < closestIntersection.distance:
                                closestIntersection = intersection

            if closestIntersection is not None:
                return closestIntersection

            else:
                node.visited = True
                if not node.isRoot:
                    self._findIntersection(ray, node.parent)
                else:
                    return None

        else:
            intersection = self._findClosestPolygonIntersection(ray, node.polygons)
            return intersection


    def _findClosestPolygonIntersection(self, ray: Ray, polygons: List[Polygon]) -> Optional[Intersection]:
        closestPolygon = None
        closestIntersection = None
        closestDistance = sys.maxsize
        for polygon in polygons:
            intersection = self._findPolygonIntersection(ray, polygon)
            if not intersection:
                continue
            distance = (intersection - ray.origin).getNorm()
            if distance < closestDistance:
                closestDistance = distance
                closestIntersection = intersection
                closestPolygon = polygon
        if not closestIntersection:
            return None
        return Intersection(closestDistance, closestIntersection, closestPolygon)

    def _findPolygonIntersection(self, ray: Ray, polygon: Polygon) -> Optional[Vector]:
        if isinstance(polygon, Triangle):
            return self._triangleIntersect.getIntersection(ray, polygon)
        if isinstance(polygon, Quad):
            return self._quadIntersect.getIntersection(ray, polygon)