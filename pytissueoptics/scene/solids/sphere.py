from pytissueoptics.scene.geometry import Vector, Triangle
from pytissueoptics.scene.geometry import primitives
from pytissueoptics.scene.materials import Material
from pytissueoptics.scene.solids import Solid
import math


class Sphere(Solid):
    """
        The Sphere is the 3D analog to the circle. Meshing a sphere requires an infinite number of vertices.
        The position refers to the vector from global origin to its centroid.
        The radius of the sphere will determine the outermost distance from its centroid.

        This class offers two possible methods to generate the sphere mesh.
        - With Quads: Specify the number of separation lines on the vertical axis and the horizontal axis of the sphere.
        - With Triangle: Specify the order of splitting. This will generate what is known as an IcoSphere.
    """

    def __init__(self,
                 radius: float = 1.0,
                 a: float = 1,
                 b: float = 1,
                 c: float = 1,
                 order: int = 4,
                 position: Vector = Vector(),
                 material: Material = Material(),
                 primitive: str = primitives.DEFAULT):

        self._radius = radius
        self._order = order

        super().__init__(position=position, material=material, vertices=[], primitive=primitive)

    @property
    def radius(self):
        return self._radius

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

        for vertex in self._vertices:
            """
            The Ellipsoid parametric equation goes as: x^2/a^2 + y^2/b^2 + z^2/c^2 =1
            A Sphere is just an ellipsoid with a = b = c.
            Bringing (x, y, z) -> (theta, phi, r) we can simply take the unit sphere and stretch it,
            since the equation becomes as follow:
            
            r^2.cos^2(theta).sin^2(phi)/a^2 + r^2.sin^2(theta).sin^2(phi)/b^2  + r^2.cos^2(phi)/c^2 = 1
            """
            vertex.normalize()
            theta, phi = self._findThetaPhi(vertex)
            vertex.multiply(self._radius)

    def _computeFirstOrderTriangleMesh(self):
        phi = (1.0 + 5.0 ** (1 / 2)) / 2.0
        xyPlaneVertices = [Vector(-1, phi, 0), Vector(1, phi, 0), Vector(-1, -phi, 0), Vector(1, -phi, 0)]
        yzPlaneVertices = [Vector(0, -1, phi), Vector(0, 1, phi), Vector(0, -1, -phi), Vector(0, 1, -phi)]
        xzPlaneVertices = [Vector(phi, 0, -1), Vector(phi, 0, 1), Vector(-phi, 0, -1), Vector(-phi, 0, 1)]
        self._vertices = [*xyPlaneVertices, *yzPlaneVertices, *xzPlaneVertices]
        V = self._vertices

        self._surfaces['Sphere'] = [Triangle(V[0], V[11], V[5]), Triangle(V[0], V[5], V[1]),
                                    Triangle(V[0], V[1], V[7]), Triangle(V[0], V[7], V[10]),
                                    Triangle(V[0], V[10], V[11]), Triangle(V[1], V[5], V[9]),
                                    Triangle(V[5], V[11], V[4]), Triangle(V[11], V[10], V[2]),
                                    Triangle(V[10], V[7], V[6]), Triangle(V[7], V[1], V[8]),
                                    Triangle(V[3], V[9], V[4]), Triangle(V[3], V[4], V[2]),
                                    Triangle(V[3], V[2], V[6]), Triangle(V[3], V[6], V[8]),
                                    Triangle(V[3], V[8], V[9]), Triangle(V[4], V[9], V[5]),
                                    Triangle(V[2], V[4], V[11]), Triangle(V[6], V[2], V[10]),
                                    Triangle(V[8], V[6], V[7]), Triangle(V[9], V[8], V[1])]

    def _computeNextOrderTriangleMesh(self):
        newSurfaces = []
        for j, surface in enumerate(self._surfaces["Sphere"]):
            ai = self._createMidVertex(surface.vertices[0], surface.vertices[1])
            bi = self._createMidVertex(surface.vertices[1], surface.vertices[2])
            ci = self._createMidVertex(surface.vertices[2], surface.vertices[0])

            self._vertices.extend([ai, bi, ci])

            newSurfaces.append(Triangle(surface.vertices[0], ai, ci))
            newSurfaces.append(Triangle(surface.vertices[1], bi, ai))
            newSurfaces.append(Triangle(surface.vertices[2], ci, bi))
            newSurfaces.append(Triangle(ai, bi, ci))

        self._surfaces["Sphere"] = newSurfaces

    @staticmethod
    def _createMidVertex(p1, p2):
        middle = Vector((p1.x + p2.x) / 2, (p1.y + p2.y) / 2, (p1.z + p2.z) / 2)
        return middle

    @staticmethod
    def _findThetaPhi(vertex: 'Vector'):
        theta = math.atan(((vertex.x**2 + vertex.y**2)**0.5)/vertex.z)
        phi = 0
        if vertex.x == 0:
            if vertex.y > 0:
                phi = math.pi/2
            elif vertex.y < 0:
                phi = -math.pi/2

        elif vertex.x > 0:
            phi = math.atan(vertex.y/vertex.x)

        elif vertex.x < 0:
            if vertex.y >= 0:
                phi = math.atan(vertex.y/vertex.x) + math.pi
            elif vertex.y < 0:
                phi = math.atan(vertex.y / vertex.x) - math.pi

        return theta, phi

    def _computeQuadMesh(self):
        raise NotImplementedError
