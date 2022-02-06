from pytissueoptics.scene.geometry import Vector, Quad, Triangle
from pytissueoptics.scene.geometry import primitives
from pytissueoptics.scene.materials import Material
from pytissueoptics.scene.solids import Solid


class Cuboid(Solid):
    """
        Also known as the Right Rectangular Prism, the Cuboid is defined by its
        width (a, b, c) in each axis (x, y, z) respectively.

        The position refers to the vector from global origin to its centroid.
        The generated mesh will be divided into the following subgroups:
        Left (-x), Right (+x), Bottom (-y), Top (+y), Front (-z), Back (+z).
    """

    def __init__(self, a: float, b: float, c: float,
                 position: Vector = Vector(0, 0, 0), material: Material = Material(),
                 primitive: str = primitives.DEFAULT, vertices=None, surfaceDict=None):
        self.shape = [a, b, c]

        if not vertices:
            vertices = [Vector(-a/2, -b/2, -c/2), Vector(a/2, -b/2, -c/2), Vector(a/2, b/2, -c/2), Vector(-a/2, b/2, -c/2),
                        Vector(-a/2, -b/2, c/2), Vector(a/2, -b/2, c/2), Vector(a/2, b/2, c/2), Vector(-a/2, b/2, c/2)]

        super().__init__(position=position, material=material, primitive=primitive,
                         vertices=vertices, surfaceDict=surfaceDict)

    def _computeTriangleMesh(self):
        V = self._vertices
        self._surfaceDict['Left'] = [Triangle(V[4], V[0], V[3]), Triangle(V[3], V[7], V[4])]
        self._surfaceDict['Right'] = [Triangle(V[1], V[5], V[6]), Triangle(V[6], V[2], V[1])]
        self._surfaceDict['Bottom'] = [Triangle(V[4], V[5], V[1]), Triangle(V[1], V[0], V[4])]
        self._surfaceDict['Top'] = [Triangle(V[3], V[2], V[6]), Triangle(V[6], V[7], V[3])]
        self._surfaceDict['Front'] = [Triangle(V[0], V[1], V[2]), Triangle(V[2], V[3], V[0])]
        self._surfaceDict['Back'] = [Triangle(V[5], V[4], V[7]), Triangle(V[7], V[6], V[5])]

    def _computeQuadMesh(self):
        V = self._vertices
        self._surfaceDict['Left'] = [Quad(V[4], V[0], V[3], V[7])]
        self._surfaceDict['Right'] = [Quad(V[1], V[5], V[6], V[2])]
        self._surfaceDict['Bottom'] = [Quad(V[4], V[5], V[1], V[0])]
        self._surfaceDict['Top'] = [Quad(V[3], V[2], V[6], V[7])]
        self._surfaceDict['Front'] = [Quad(V[0], V[1], V[2], V[3])]
        self._surfaceDict['Back'] = [Quad(V[5], V[4], V[7], V[6])]

    def stack(self, other: 'Cuboid', onSurface: str = 'Top') -> 'Cuboid':
        """
        Basic implementation for stacking cuboids along an axis.

        For example, stacking on 'Top' will move the other cuboid on top of the this cuboid. They will now share
         the same mesh at the interface and inside/outside materials at the interface will be properly defined.
         This will return a new cuboid that represents the stack, with a new 'Interface<i>' surface group.

        Limitations:
            - Requires cuboids with the same shape except along the stack axis.
            - Cannot stack another stack along its stacked axis (ill-defined interface material).
            - Expected behavior not guaranteed for pre-rotated cuboids.
        """
        assert onSurface in self._surfaceDict.keys(), f"Available surfaces to stack on are: {self._surfaceDict.keys()}"

        surfacePairs = [('Left', 'Right'), ('Bottom', 'Top'), ('Front', 'Back')]
        axis = max(axis if onSurface in surfacePair else -1 for axis, surfacePair in enumerate(surfacePairs))
        assert self.shape[(axis + 1) % 3] == other.shape[(axis + 1) % 3] and \
               self.shape[(axis + 2) % 3] == other.shape[(axis + 2) % 3], \
               f"Stacking of mismatched surfaces is not supported."

        relativePosition = [0, 0, 0]
        relativePosition[axis] = self.shape[axis]/2 + other.shape[axis]/2
        relativePosition = Vector(*relativePosition)
        other.translateTo(self.position + relativePosition)

        # Set new interface material and remove duplicate surfaces
        onSurfaceIndex = surfacePairs[axis].index(onSurface)
        oppositeSurfaceKey = surfacePairs[axis][(onSurfaceIndex + 1) % 2]
        oppositeMaterial = other._surfaceDict[oppositeSurfaceKey][0].insideMaterial
        for oppositeSurface in other._surfaceDict[oppositeSurfaceKey]:
            assert oppositeSurface.insideMaterial == oppositeMaterial, \
                "Ill-defined interface material: Cannot stack another stack along it's stacked axis."
        self._setOutsideMaterial(oppositeMaterial, faceKey=onSurface)

        other._surfaceDict[oppositeSurfaceKey] = self._surfaceDict[onSurface]

        # Define new stack as a Cuboid
        relativeStackCentroid = [0, 0, 0]
        relativeStackCentroid[axis] = other.shape[axis] / 2
        stackCentroid = self.position + Vector(*relativeStackCentroid)
        stackShape = self.shape.copy()
        stackShape[axis] += other.shape[axis]

        stackVertices = self._vertices
        newVertices = [vertex for vertex in other._vertices if vertex not in self._vertices]
        stackVertices.extend(newVertices)
        # subtracting stackCentroid from all vertices because solid creation will translate back to stack centroid.
        for vertex in stackVertices:
            vertex.subtract(stackCentroid)

        interfaceKeys = [key for key in self._surfaceDict.keys() if "Interface" in key]
        interfaceIndex = len(interfaceKeys)
        stackSurfaces = {onSurface: other._surfaceDict[onSurface],
                         oppositeSurfaceKey: self._surfaceDict[oppositeSurfaceKey],
                         f'Interface{interfaceIndex}': self._surfaceDict[onSurface]}
        for interfaceKey in interfaceKeys:
            stackSurfaces[interfaceKey] = self._surfaceDict[interfaceKey]
        otherInterfaceKeys = [key for key in other._surfaceDict.keys() if "Interface" in key]
        for i, otherInterfaceKey in enumerate(otherInterfaceKeys):
            newOtherInterfaceIndex = interfaceIndex + 1 + i
            stackSurfaces[f'Interface{newOtherInterfaceIndex}'] = other._surfaceDict[otherInterfaceKey]
        surfaceKeysLeft = surfacePairs[(axis + 1) % 3] + surfacePairs[(axis + 2) % 3]
        for surfaceKey in surfaceKeysLeft:
            stackSurfaces[surfaceKey] = self._surfaceDict[surfaceKey] + other._surfaceDict[surfaceKey]

        # todo: refactor
        # todo: Solid.material is somewhat useless (except for solid creation) and wrong...
        #  The true material reference is only at surface level.

        return Cuboid(*stackShape, position=stackCentroid, vertices=stackVertices, surfaceDict=stackSurfaces,
                      material=None, primitive=self._primitive)


if __name__ == "__main__":
    from pytissueoptics.scene.viewer.mayavi import MayaviSolid, MayaviViewer

    cuboid1 = Cuboid(5, 1, 4, position=Vector(4, 0.5, 0))
    cuboid2 = Cuboid(5, 2, 4, position=Vector(4, 1, -6))
    cuboid3 = Cuboid(2, 3, 4, position=Vector(-2, 1.5, -3))

    cuboidStack = cuboid1.stack(cuboid2).stack(cuboid3, onSurface='Right')

    # cuboid1Mayavi = MayaviSolid(cuboid1)
    # cuboid2Mayavi = MayaviSolid(cuboid2)
    # cuboid3Mayavi = MayaviSolid(cuboid3)
    cuboidStackMayavi = MayaviSolid(cuboidStack)

    viewer = MayaviViewer()
    # viewer.addMayaviSolid(cuboid1Mayavi, representation="wireframe")
    # viewer.addMayaviSolid(cuboid2Mayavi, representation="wireframe")
    # viewer.addMayaviSolid(cuboid3Mayavi, representation="wireframe")
    viewer.addMayaviSolid(cuboidStackMayavi, representation="wireframe")
    viewer.show()
