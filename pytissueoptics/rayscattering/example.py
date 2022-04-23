from pytissueoptics.rayscattering import *
from pytissueoptics.rayscattering.tissues import PhantomTissue
from pytissueoptics.scene import Vector, Logger
import numpy as np

np.random.seed(15)

tissue = PhantomTissue()
source = PencilSource(position=Vector(0, 0, -1),
                      direction=Vector(0, 0, 1), N=2000)
logger = Logger()

source.propagate(tissue, logger=logger)

stats = Stats(logger, tissue)
stats.showEnergy3D()
stats.showEnergy3DOfSurfaces()
stats.showEnergy2D()
stats.showEnergy2D("middleLayer", bins=50)
stats.showEnergy2D("middleLayer", "interface1", projection='z', bins=50, logScale=True)
stats.showEnergy1D(bins=100)
