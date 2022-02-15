from math import cos, sin, acos, atan, pi, sqrt

import numpy as np

from pytissueoptics.scene.geometry import Vector, Triangle, primitives, utils
from pytissueoptics.scene.materials import Material
from pytissueoptics.scene.solids import Solid


class Ellipsoid(Solid):
    """
        We take the unit sphere, then calculate the theta, phi position of each vertex (with ISO mathematical
        convention). Then we apply the ellipsoid formula in the spherical coordinate to isolate the component R.
        We then calculate the difference the ellipsoid would with the unit sphere for this theta,phi and
        then .add() or .subtract() the corresponding vector.
    """

    def __init__(self, a: float = 1, b: float = 1, c: float = 1, order: int = 3,
                 position: Vector = Vector(0, 0, 0), material: Material = None,
                 primitive: str = primitives.DEFAULT):

        self._a = a
        self._b = b
        self._c = c
        self._order = order

        super().__init__(position=position, material=material, primitive=primitive, vertices=[])

    def _computeTriangleMesh(self):
        """
        The most precise sphere approximation is the IcoSphere, which is generated from the platonic solid,
        the Icosahedron. It is built with 20 equilateral triangles with exactly the same angle between each.
        From Euler's method to generate the vertex for the icosahedron, we cross 3 perpendicular planes,
        with lenght=2 and width=2*phi. Joining adjscent vertices will produce the Icosahedron.

        From the Icosahedron, we can split each face in 4 triangles, in a recursive manner, to obtain an IcoSphere.
        The method goes as follow:
        1 - Find each mid-point between two connecting vertices on a triangle
        2 - Normalize those new points to project them onto the unit sphere.
        3 - Connect the new vertices in a way to make 4 new triangles.
        4 - Do these steps for each triangle (This will lead to redundant calculation, I am aware)
        5 - Replace the old surfaces by the new surfaces
        """

        self._computeFirstOrderTriangleMesh()

        for i in range(0, self._order):
            self._computeNextOrderTriangleMesh()

        self._setVerticesPositionsFromCenter()

    def _computeFirstOrderTriangleMesh(self):
        phi = (1.0 + 5.0 ** (1 / 2)) / 2.0
        xyPlaneVertices = [Vector(-1, phi, 0), Vector(1, phi, 0), Vector(-1, -phi, 0), Vector(1, -phi, 0)]
        yzPlaneVertices = [Vector(0, -1, phi), Vector(0, 1, phi), Vector(0, -1, -phi), Vector(0, 1, -phi)]
        xzPlaneVertices = [Vector(phi, 0, -1), Vector(phi, 0, 1), Vector(-phi, 0, -1), Vector(-phi, 0, 1)]
        self._vertices = [*xyPlaneVertices, *yzPlaneVertices, *xzPlaneVertices]
        V = self._vertices

        self._surfaces.add("Sphere", [Triangle(V[0], V[11], V[5]), Triangle(V[0], V[5], V[1]),
                                      Triangle(V[0], V[1], V[7]), Triangle(V[0], V[7], V[10]),
                                      Triangle(V[0], V[10], V[11]), Triangle(V[1], V[5], V[9]),
                                      Triangle(V[5], V[11], V[4]), Triangle(V[11], V[10], V[2]),
                                      Triangle(V[10], V[7], V[6]), Triangle(V[7], V[1], V[8]),
                                      Triangle(V[3], V[9], V[4]), Triangle(V[3], V[4], V[2]),
                                      Triangle(V[3], V[2], V[6]), Triangle(V[3], V[6], V[8]),
                                      Triangle(V[3], V[8], V[9]), Triangle(V[4], V[9], V[5]),
                                      Triangle(V[2], V[4], V[11]), Triangle(V[6], V[2], V[10]),
                                      Triangle(V[8], V[6], V[7]), Triangle(V[9], V[8], V[1])])

    def _computeNextOrderTriangleMesh(self):
        newPolygons = []
        for j, polygon in enumerate(self.getPolygons()):
            ai = self._createMidVertex(polygon.vertices[0], polygon.vertices[1])
            bi = self._createMidVertex(polygon.vertices[1], polygon.vertices[2])
            ci = self._createMidVertex(polygon.vertices[2], polygon.vertices[0])

            self._vertices.extend([ai, bi, ci])

            newPolygons.append(Triangle(polygon.vertices[0], ai, ci))
            newPolygons.append(Triangle(polygon.vertices[1], bi, ai))
            newPolygons.append(Triangle(polygon.vertices[2], ci, bi))
            newPolygons.append(Triangle(ai, bi, ci))

        self._surfaces.setPolygons("Sphere", newPolygons)

    @staticmethod
    def _createMidVertex(p1, p2):
        middle = Vector((p1.x + p2.x) / 2, (p1.y + p2.y) / 2, (p1.z + p2.z) / 2)
        return middle

    def _setVerticesPositionsFromCenter(self):
        """
        The Ellipsoid parametric equation goes as: x^2/a^2 + y^2/b^2 + z^2/c^2 =1
        A Sphere is just an ellipsoid with a = b = c.
        Bringing (x, y, z) -> (theta, phi, r) we can simply take the unit sphere and stretch it,
        since the equation becomes as follow:

        r^2.cos^2(theta).sin^2(phi)/a^2 + r^2.sin^2(theta).sin^2(phi)/b^2  + r^2.cos^2(phi)/c^2 = 1
        """
        for vertex in self._vertices:
            vertex.normalize()
            r = self._radiusTowards(vertex)
            distanceFromUnitSphere = (r - 1.0)
            vertex.add(vertex * distanceFromUnitSphere)

    @staticmethod
    def _findThetaPhi(vertex: 'Vector'):
        phi = acos(vertex.z / (vertex.x ** 2 + vertex.y ** 2 + vertex.z ** 2))
        theta = 0
        if vertex.x == 0.0:
            if vertex.y > 0.0:
                theta = pi / 2

            elif vertex.y < 0.0:
                theta = -pi / 2

        elif vertex.x > 0.0:
            theta = atan(vertex.y / vertex.x)

        elif vertex.x < 0.0:
            if vertex.y >= 0.0:
                theta = atan(vertex.y / vertex.x) + pi

            elif vertex.y < 0.0:
                theta = atan(vertex.y / vertex.x) - pi

        return theta, phi
    
    def _radiusTowards(self, vertex):
        theta, phi = self._findThetaPhi(vertex)
        return sqrt(1 / ((cos(theta) ** 2 * sin(phi) ** 2) / self._a ** 2 + (
                sin(theta) ** 2 * sin(phi) ** 2) / self._b ** 2 + cos(phi) ** 2 / self._c ** 2))

    def _computeQuadMesh(self):
        raise NotImplementedError

    def contains(self, *vertices: Vector) -> bool:
        """ Only returns true if all vertices are inside the minimum radius of the ellipsoid
        towards each vertex direction (more restrictive with low order ellipsoids). """
        verticesArray = np.asarray([vertex.array for vertex in vertices])
        relativeVerticesArray = verticesArray - self.position.array

        if self._orientation:
            relativeVerticesArray = utils.rotateVerticesArray(relativeVerticesArray, self._orientation, inverse=True)

        for relativeVertexArray in relativeVerticesArray:
            relativeVertex = Vector(*relativeVertexArray)
            vertexRadius = relativeVertex.getNorm()
            if vertexRadius == 0:
                continue
            minRadius = self._getMinimumRadiusTowards(relativeVertex)
            if vertexRadius >= minRadius:
                return False
        return True

    def _getRadiusError(self) -> float:
        aPolygon = self.surfaces.getPolygons()[0]
        centerVertex = Vector(0, 0, 0)
        for vertex in aPolygon.vertices:
            centerVertex.add(vertex)
        centerVertex.divide(len(aPolygon.vertices))
        centerVertex.subtract(self.position)

        localMinimumRadius = centerVertex.getNorm()
        localTrueRadius = self._radiusTowards(centerVertex)
        return abs(localTrueRadius - localMinimumRadius) / localTrueRadius

    def _getMinimumRadiusTowards(self, vertex) -> float:
        return (1 - self._getRadiusError()) * self._radiusTowards(vertex)
