try:
    from mayavi import mlab
except ImportError:
    pass

from pytissueoptics.scene.viewer.mayavi.MayaviSolid import MayaviSolid
from pytissueoptics.scene.solids import Sphere, Cuboid
from pytissueoptics.scene.geometry import Vector


class MayaviViewer:
    def __init__(self):
        self._scenes = {"DefaultScene": {"figure": mlab.figure(1, bgcolor=(0.11, 0.11, 0.11), fgcolor=(0.9, 0.9, 0.9)), "Solids": [], }}
        self._view = {"azimuth": 0, "zenith": 0, "distance": None, "pointingTowards": None, "roll": None}

    def addMayaviSolid(self, other: 'MayaviSolid', representation="wireframe", line_width=0.25):
        self._scenes["DefaultScene"]["Solids"].append(other)
        mlab.triangular_mesh(*other.meshComponents, representation=representation, line_width=line_width, colormap="viridis")

    def _assignViewPoint(self):
        azimuth, elevation, distance, towards, roll = (self._view[key] for key in self._view)
        mlab.view(azimuth, elevation, distance, towards, roll)

    def show(self):
        self._assignViewPoint()
        mlab.show()


if __name__ == "__main__":
    sphere1 = MayaviSolid(Sphere(order=2))
    cuboid1 = MayaviSolid(Cuboid(1, 3, 3, position=Vector(4, 0, 0)))
    viewer = MayaviViewer()
    viewer.addMayaviSolid(sphere1, representation="surface")
    viewer.addMayaviSolid(cuboid1, representation="surface")

    viewer.show()
