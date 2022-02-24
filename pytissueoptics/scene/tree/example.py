from pytissueoptics.scene.scene import Scene
from pytissueoptics.scene.geometry import Vector
from pytissueoptics.scene.solids import Cuboid, Sphere
from pytissueoptics.scene.tree import SpacePartition
from pytissueoptics.scene.tree.treeConstructor.binary import SAHWideAxisTreeConstructor
from pytissueoptics.scene.viewer import MayaviViewer

import time


cuboid1 = Cuboid(a=1, b=3, c=1, position=Vector(4, -2, 6))
cuboid2 = Cuboid(1, 1, 1, position=Vector(-2, -2, 0))
sphere = Sphere(position=Vector(3, 3, 3), order=4)
scene = Scene([cuboid1, cuboid2, sphere])

t0 = time.time()
kdTree = SpacePartition(scene.getBoundingBox(), scene.getPolygons(), constructor=SAHWideAxisTreeConstructor(),
                        maxDepth=10, minLeafSize=2)
t1 = time.time()

bBoxes = kdTree.getLeafBoundingBoxesAsCuboids()

print(f"Scene Poly Count:{len(scene.getPolygons())}\n"
      f"Min Leaf Size:{kdTree.minLeafSize}\n"
      f"Max Tree Depth:{kdTree.maxDepth}\n"
      f"Total Node:{kdTree.getNodeCount()}\n"
      f"Total Leaf Node:{kdTree.getLeafCount()}\n"
      f"Tree Render Time:{t1 - t0}s")

viewer = MayaviViewer()
viewer.add(*scene.getSolids(), representation="mesh", lineWidth=0.1)
viewer.add(*bBoxes, representation="surface", lineWidth=0.1, opacity=0.25)
viewer.show()
