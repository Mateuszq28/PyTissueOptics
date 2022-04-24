import unittest
import numpy as np

from pytissueoptics.rayscattering import Photon, PencilSource
from pytissueoptics.rayscattering.materials import ScatteringMaterial
from pytissueoptics.rayscattering.opencl.CLSource import CLPencilSource
from pytissueoptics.rayscattering.tissues.rayScatteringScene import RayScatteringScene
from pytissueoptics.scene import Logger

np.random.seed(15)


@unittest.skip("Only for OPENCL compatible devices")
class TestPropagation(unittest.TestCase):
    def test_whenPropagatingCPUandGPUPhotons_loggerShouldContainSamePositionsAndValues(self):
        worldMaterial = ScatteringMaterial(mu_s=30, mu_a=0.1, g=0.8, index=1.4)
        myLoggerCPU = Logger()
        mySceneCPU = RayScatteringScene([])
        mySourceCPU = PencilSource(N=1)
        mySourceCPU.propagate(mySceneCPU, worldMaterial=worldMaterial, logger=myLoggerCPU)

        myLoggerGPU = Logger()
        mySourceGPU = CLPencilSource(N=1)
        mySourceGPU.propagate(worldMaterial=worldMaterial, logger=myLoggerGPU)

        for i in range(len(myLoggerCPU.dataPoints)):
            self.assertTrue(myLoggerCPU.dataPoints[i].position, myLoggerGPU.dataPoints[i].position)
            self.assertTrue(myLoggerCPU.dataPoints[i].value, myLoggerGPU.dataPoints[i].value)
