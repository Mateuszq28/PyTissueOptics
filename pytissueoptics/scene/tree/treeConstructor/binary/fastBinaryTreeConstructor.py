from typing import List, Tuple
from dataclasses import dataclass
from math import isclose
import sys

from pytissueoptics.scene.geometry import Polygon, BoundingBox, Quad, Vector
from pytissueoptics.scene.tree import Node
from pytissueoptics.scene.intersection import Ray
from pytissueoptics.scene.intersection.quadIntersect import MollerTrumboreQuadIntersect
from pytissueoptics.scene.tree.treeConstructor import TreeConstructor, SplitNodeResult


@dataclass
class SAHSearchResult:
    leftPolygons: List[Polygon]
    rightPolygons: List[Polygon]
    toSplitPolygons: List[Polygon]
    leftBbox: BoundingBox
    rightBbox: BoundingBox
    nLeft: int
    nRight: int
    leftSAH: float
    rightSAH: float
    splitAxis : str
    splitValue: float


class FastBinaryTreeConstructor(TreeConstructor):
    def __init__(self):
        self._traversalCost = 8
        self._intersectionCost = 1
        self._reductionFactor = 0.8
        self._nbOfPlanes = 20
        self._quadIntersector = MollerTrumboreQuadIntersect()

    def _splitNode(self, node: Node) -> SplitNodeResult:
        nodeBbox = node.bbox
        nodePolygons = node.polygons
        polygonsBbox = BoundingBox.fromPolygons(nodePolygons)
        SAHResult = self._searchMinSAH(polygonsBbox, nodePolygons, self._nbOfPlanes)
        if self._checkIfWorthNodeSplit(nodeBbox.getArea(), SAHResult):

            #normal, point = self._makeSplitPlane2(SAHResult.splitAxis, SAHResult.splitValue)
            #goingLeft, goingRight = self._splitPolygons2(SAHResult.toSplitPolygons, normal, point, SAHResult.splitAxis, SAHResult.splitValue)

            plane = self._makeSplitPlane(SAHResult.splitAxis, SAHResult.splitValue)
            goingLeft, goingRight = self._splitPolygons(SAHResult.toSplitPolygons, plane, SAHResult.splitAxis,
                                                         SAHResult.splitValue)

            SAHResult.leftPolygons.extend(goingLeft)
            SAHResult.rightPolygons.extend(goingRight)
            return SplitNodeResult(False, "", 0, [SAHResult.leftBbox, SAHResult.rightBbox], [SAHResult.leftPolygons, SAHResult.rightPolygons])
        else:
            return SplitNodeResult(True, None, None, None, None)

    def _checkIfWorthNodeSplit(self, nodeSA: float, SAHResult: SAHSearchResult):
        approximatedSplitCost = self._traversalCost + self._intersectionCost * (
                    (SAHResult.leftSAH + SAHResult.rightSAH) / nodeSA)
        currentTraversalCost = self._intersectionCost * (SAHResult.nLeft + SAHResult.nRight)
        if approximatedSplitCost < currentTraversalCost:
            nodeSplit = True
        else:
            nodeSplit = False
        return nodeSplit

    @staticmethod
    def _makeSplitPlane(splitAxis: str, splitValue: float) -> Quad:
        plus = sys.maxsize/2
        minus = -sys.maxsize/2
        if splitAxis == "x":
            splitPoints = [Vector(splitValue, plus, plus),
                           Vector(splitValue, plus, minus),
                           Vector(splitValue, minus, minus),
                           Vector(splitValue, minus, plus)]
            return Quad(*splitPoints)
        elif splitAxis == "y":
            splitPoints = [Vector(plus, splitValue, plus),
                           Vector(plus, splitValue, minus),
                           Vector(minus, splitValue, minus),
                           Vector(minus, splitValue, plus)]
            return Quad(*splitPoints)
        elif splitAxis == "z":
            splitPoints = [Vector(plus, plus, splitValue),
                           Vector(plus, minus, splitValue),
                           Vector(minus, minus, splitValue),
                           Vector(minus, plus,  splitValue)]
            return Quad(*splitPoints)

    @staticmethod
    def _makeSplitPlane2(splitAxis: str, splitValue: float) -> Tuple[Vector, Vector]:
        if splitAxis == "x":
            normal = Vector(1, 0, 0)
            planePoint = Vector(splitValue, 0, 0)
            return normal, planePoint
        elif splitAxis == "y":
            normal = Vector(0, 1, 0)
            planePoint = Vector(0, splitValue, 0)
            return normal, planePoint
        elif splitAxis == "z":
            normal = Vector(0, 0, 1)
            planePoint = Vector(0, 0, splitValue)
            return normal, planePoint

    def _searchMinSAH(self, bbox, polygons, nbOfPlanes):
        SAHresult = None
        minSAH = sys.maxsize
        for splitAxis in ["x", "y", "z"]:
            aMin, aMax = bbox.getAxisLimits(splitAxis)
            step = bbox.getAxisWidth(splitAxis) / (nbOfPlanes + 1)
            for i in range(0, nbOfPlanes):
                splitValue = aMin + i * step
                left, right, both = self._classifyPolygons(splitValue, splitAxis, polygons)
                leftBbox = bbox.copy()
                leftBbox.update(splitAxis, "max", splitValue)
                rightBbox = bbox.copy()
                rightBbox.update(splitAxis, "min", splitValue)
                nLeft = len(left) + len(both)
                nRight = len(right) + len(both)
                leftSAH = nLeft * leftBbox.getArea()
                rightSAH = nRight * rightBbox.getArea()
                newSAH = leftSAH + rightSAH
                if (nLeft == 0 or nRight == 0) and len(both) == 0:
                    newSAH *= self._reductionFactor
                if newSAH < minSAH:
                    minSAH = newSAH
                    SAHresult = SAHSearchResult(left, right, both, leftBbox, rightBbox, nLeft, nRight, leftSAH,
                                                rightSAH, splitAxis, splitValue)
        return SAHresult

    @staticmethod
    def _intersectPlaneWithRay(normal: Vector, planePoint: Vector, ray: Ray, tol=1e-6):
        """
        algorithm from scratchpixel.com
        1. normal.dot(direction), to check if plane and are are coplanar
        2. the dot product of two perpendicular vectors is equal to 0  | (normal.dot(planePoint - origin)) = 0
        3. we parametrize the ray equation as | origin + direction * t = planePoint
        4. we solve for t.
        5. in our case, the hit point has to be within the predefined polygon, so we verify 't' with the ray.length
        """
        coplanar = normal.dot(ray.direction)
        if abs(coplanar) > tol:
            inPlane = planePoint - ray.origin
            t = inPlane.dot(normal) / coplanar
            hit = ray.origin + ray.direction * t
            if (hit-ray.origin).getNorm() <= ray.length:
                return hit
        return None

    def _splitPolygons(self, polygonsToSplit: List[Polygon], plane: Quad, splitAxis, splitValue):
        left = []
        right = []
        for polygon in polygonsToSplit:
            polygonRays = self._getPolygonAsRays(polygon)
            intersectionPoints = []
            leftVertices = []
            rightVertices = []
            for ray in polygonRays:
                if splitAxis == "x":
                    rayValue = ray.origin.x
                elif splitAxis == "y":
                    rayValue = ray.origin.y
                else:
                    rayValue = ray.origin.z

                if isclose(rayValue, splitValue, abs_tol=1e-6):
                    intersectionPoints.append(ray.origin)
                elif rayValue < splitValue:
                    leftVertices.append(ray.origin)
                else:
                    rightVertices.append(ray.origin)
                intersectionPoint = self._quadIntersector.getIntersection(ray, plane)
                if intersectionPoint:
                    intersectionPoints.append(intersectionPoint)

            if leftVertices:
                leftVertices.extend(intersectionPoints)
                left.append(Polygon(vertices=leftVertices))
            if rightVertices:
                rightVertices.extend(intersectionPoints)
                right.append(Polygon(vertices=rightVertices))
        return left, right

    def _splitPolygons2(self, polygonsToSplit: List[Polygon], planeNormal: Vector, planePoint: Vector, splitAxis, splitValue):
        left = []
        right = []
        for polygon in polygonsToSplit:
            polygonRays = self._getPolygonAsRays(polygon)
            intersectionPoints = []
            leftVertices = []
            rightVertices = []
            for ray in polygonRays:
                if splitAxis == "x":
                    rayValue = ray.origin.x
                elif splitAxis == "y":
                    rayValue = ray.origin.y
                else:
                    rayValue = ray.origin.z

                if isclose(rayValue, splitValue, abs_tol=1e-6):
                    intersectionPoints.append(ray.origin)
                elif rayValue < splitValue:
                    leftVertices.append(ray.origin)
                else:
                    rightVertices.append(ray.origin)
                intersectionPoint = self._intersectPlaneWithRay(planeNormal, planePoint, ray)
                if intersectionPoint:
                    intersectionPoints.append(intersectionPoint)

            if leftVertices:
                leftVertices.extend(intersectionPoints)
                left.append(Polygon(vertices=leftVertices))
            if rightVertices:
                rightVertices.extend(intersectionPoints)
                right.append(Polygon(vertices=rightVertices))
        return left, right

    @staticmethod
    def _getPolygonAsRays(polygon):
        polygonRays = []
        for i, vertex in enumerate(polygon.vertices):
            if i == len(polygon.vertices) - 1:
                nextVertex = polygon.vertices[0]
            else:
                nextVertex = polygon.vertices[i + 1]
            direction = nextVertex - vertex
            polygonRays.append(Ray(vertex, direction, direction.getNorm()))
        return polygonRays

    @staticmethod
    def _classifyPolygons(splitLine: float, splitAxis: str, polygons: List[Polygon]):
        goingLeft = []
        goingRight = []
        toBeSplit = []

        for polygon in polygons:
            limits = polygon.bbox.getAxisLimits(splitAxis)
            if limits[0] < splitLine and limits[1] < splitLine:
                goingLeft.append(polygon)
            elif limits[0] > splitLine and limits[1] > splitLine:
                goingRight.append(polygon)
            else:
                toBeSplit.append(polygon)

        return [goingLeft, goingRight, toBeSplit]

    def growTree(self, node: Node, maxDepth: int, minLeafSize: int):
        if node.depth >= maxDepth or len(node.polygons) <= minLeafSize:
            return

        splitNodeResult = self._splitNode(node)
        if splitNodeResult.stopCondition:
            return

        for i, polygonGroup in enumerate(splitNodeResult.polygonGroups):
            if len(polygonGroup) <= 0:
                continue
            childNode = Node(parent=node, polygons=polygonGroup, bbox=splitNodeResult.bboxes[i], depth=node.depth + 1)
            node.children.append(childNode)
            self.growTree(childNode, maxDepth, minLeafSize)
