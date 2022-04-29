import os
import unittest
import pyopencl as cl
import pyopencl.tools
import numpy as np
from numpy.lib import recfunctions as rfn
import matplotlib.pyplot as plt

from pytissueoptics.scene import Vector


class TestCLPropagationKernels(unittest.TestCase):
    def setUp(self):
        randomKernel = open(os.path.dirname(os.path.abspath(__file__)) + "{0}..{0}src{0}random.c".format(os.sep)).read()
        propagationKernel = open(os.path.dirname(os.path.abspath(__file__)) + "{0}..{0}src{0}propagation.c".format(os.sep)).read()
        vectorKernel = open(os.path.dirname(os.path.abspath(__file__)) + "{0}..{0}src{0}vector_operators.c".format(os.sep)).read()
        self.ctx = cl.create_some_context()
        self.queue = cl.CommandQueue(self.ctx)
        self.device = self.ctx.devices[0]
        self.mf = cl.mem_flags
        c_decl = self._makeTypes()
        self.program = cl.Program(self.ctx, c_decl + randomKernel + vectorKernel + propagationKernel).build()

    def _makeTypes(self):
        def makePhotonType():
            photonStruct = np.dtype(
                [("position", cl.cltypes.float4),
                 ("direction", cl.cltypes.float4),
                 ("er", cl.cltypes.float4),
                 ("weight", cl.cltypes.float),
                 ("material_id", cl.cltypes.uint)])
            name = "photonStruct"
            photonStruct, c_decl_photon = cl.tools.match_dtype_to_c_struct(self.device, name, photonStruct)
            photon_dtype = cl.tools.get_or_register_dtype(name, photonStruct)
            return photon_dtype, c_decl_photon

        def makeMaterialType():
            materialStruct = np.dtype(
                [("mu_s", cl.cltypes.float),
                 ("mu_a", cl.cltypes.float),
                 ("mu_t", cl.cltypes.float),
                 ("g", cl.cltypes.float),
                 ("n", cl.cltypes.float),
                 ("albedo", cl.cltypes.float),
                 ("material_id", cl.cltypes.uint)])
            name = "materialStruct"
            materialStruct, c_decl_mat = cl.tools.match_dtype_to_c_struct(self.device, name, materialStruct)
            material_dtype = cl.tools.get_or_register_dtype(name, materialStruct)
            return material_dtype, c_decl_mat

        def makeLoggerType():
            loggerStruct = np.dtype(
                [("delta_weight", cl.cltypes.float),
                 ("x", cl.cltypes.float),
                 ("y", cl.cltypes.float),
                 ("z", cl.cltypes.float)])
            name = "loggerStruct"
            loggerStruct, c_decl_logger = cl.tools.match_dtype_to_c_struct(self.device, name, loggerStruct)
            logger_dtype = cl.tools.get_or_register_dtype(name, loggerStruct)
            return logger_dtype, c_decl_logger

        photon_dtype, c_decl_photon = makePhotonType()
        material_dtype, c_decl_mat = makeMaterialType()
        logger_dtype, c_decl_logger = makeLoggerType()
        return c_decl_photon + c_decl_mat + c_decl_logger

    def makeRandomVectorsAndBuffers(self, N):
        rng = np.random.default_rng()
        randomErValues = rng.random((N, 3), dtype=np.float32)
        float4AddOn = np.zeros((N, 1), dtype=np.float32)
        CPU_VectorEr = [Vector(*randomErValues[i, :]) for i in range(N)]
        randomErValues = np.append(randomErValues, float4AddOn, axis=1)
        randomErValuesFloat4 = [cl.cltypes.make_float4(*randomErValues[i, :]) for i in range(N)]
        HOST_ErVectors = np.array(randomErValuesFloat4, dtype=cl.cltypes.float4)
        DEVICE_ErVectors = cl.Buffer(self.ctx, self.mf.READ_WRITE | self.mf.COPY_HOST_PTR, hostbuf=HOST_ErVectors)
        return CPU_VectorEr, HOST_ErVectors, DEVICE_ErVectors

    def makeRandomScalarsAndBuffers(self, N):
        rng = np.random.default_rng()
        randomScalarValues = rng.uniform(low=0.0000, high=1.0, size=N)
        CPU_scalarValues = [np.float32(randomScalarValues[i]) for i in range(N)]
        HOST_ScalarValues = np.array(randomScalarValues, dtype=np.float32)
        DEVICE_ScalarValues = cl.Buffer(self.ctx, self.mf.READ_WRITE | self.mf.COPY_HOST_PTR, hostbuf=HOST_ScalarValues)
        return CPU_scalarValues, HOST_ScalarValues, DEVICE_ScalarValues

    @staticmethod
    def getScatteringTheta(rndValue, g):
        if g == 0:
            cost = 2 * rndValue - 1
        else:
            temp = (1 - g * g) / (1 - g + 2 * g * rndValue)
            cost = (1 + g * g - temp * temp) / (2 * g)
        return np.arccos(cost)

    @staticmethod
    def getScatteringDistance(rndValue, mu_t):
        if mu_t == 0:
            return np.inf

        if rndValue == 0:
            raise ValueError("rndValue cannot be 0")
        return -np.log(rndValue) / mu_t

    def test_whenGetScatteringAngleTheta_GPU_and_CPU_shouldReturnSameValues(self):
        N = 500
        g = 0.8
        CPU_rndValues, HOST_rndValues, DEVICE_rndValues = self.makeRandomScalarsAndBuffers(N)
        HOST_angleResults = np.zeros(N, dtype=np.float32)
        DEVICE_angleResults = cl.Buffer(self.ctx, self.mf.READ_WRITE | self.mf.COPY_HOST_PTR, hostbuf=HOST_angleResults)

        CPU_angleResults = np.array([self.getScatteringTheta(rndValue, g) for rndValue in CPU_rndValues])

        self.program.getScatteringAngleThetaKernel(self.queue, HOST_rndValues.shape, None, DEVICE_angleResults, DEVICE_rndValues,  np.float32(g))
        cl.enqueue_copy(self.queue, HOST_angleResults, DEVICE_angleResults)

        GPU_angleResults = HOST_angleResults

        self.assertTrue(np.all(np.isclose(CPU_angleResults, GPU_angleResults, atol=1e-3)))

    def test_whenGetScatteringAnglePhi_GPU_and_CPU_shouldReturnSameValues(self):
        N = 50000
        CPU_rndValues, HOST_rndValues, DEVICE_rndValues = self.makeRandomScalarsAndBuffers(N)
        HOST_angleResults = np.zeros(N, dtype=np.float32)
        DEVICE_angleResults = cl.Buffer(self.ctx, self.mf.READ_WRITE | self.mf.COPY_HOST_PTR, hostbuf=HOST_angleResults)

        CPU_angleResults = np.array([rndValue * 2 * np.pi for rndValue in CPU_rndValues])

        self.program.getScatteringAnglePhiKernel(self.queue, HOST_rndValues.shape, None, DEVICE_angleResults, DEVICE_rndValues)
        cl.enqueue_copy(self.queue, HOST_angleResults, DEVICE_angleResults)

        GPU_angleResults = HOST_angleResults

        self.assertTrue(np.all(np.isclose(CPU_angleResults, GPU_angleResults, atol=1e-3)))

    def test_whenGetScatteringDistance_GPU_and_CPU_shouldReturnSameValues(self):
        N = 500
        mu_t = 30.1
        CPU_rndValues, HOST_rndValues, DEVICE_rndValues = self.makeRandomScalarsAndBuffers(N)
        HOST_distanceResults = np.zeros(N, dtype=np.float32)
        DEVICE_distanceResults = cl.Buffer(self.ctx, self.mf.READ_WRITE | self.mf.COPY_HOST_PTR, hostbuf=HOST_distanceResults)

        CPU_distanceResults = np.array([self.getScatteringDistance(rndValue, mu_t) for rndValue in CPU_rndValues])

        self.program.getScatteringDistanceKernel(self.queue, HOST_rndValues.shape, None, DEVICE_distanceResults, DEVICE_rndValues,  np.float32(mu_t))
        cl.enqueue_copy(self.queue, HOST_distanceResults, DEVICE_distanceResults)

        GPU_distanceResults = HOST_distanceResults
        self.assertTrue(np.all(np.isclose(CPU_distanceResults, GPU_distanceResults, atol=1e-3)))

    def test_whenRotateAroundVector_GPU_and_CPU_shouldReturnSameValues(self):
        N = 500

        CPU_ErVectors, HOST_ErVectors, DEVICE_ErVectors = self.makeRandomVectorsAndBuffers(N)
        CPU_AxisVectors, HOST_AxisVectors, DEVICE_AxisVectors = self.makeRandomVectorsAndBuffers(N)
        CPU_PhiValues, HOST_PhiValues, DEVICE_PhiValues = self.makeRandomScalarsAndBuffers(N)

        for vector in CPU_AxisVectors:
            vector.normalize()
        for i, vector in enumerate(CPU_ErVectors):
            vector.rotateAround(CPU_AxisVectors[i], CPU_PhiValues[i])
        CPU_VectorErResults = np.array([[vector.x, vector.y, vector.z] for vector in CPU_ErVectors])

        self.program.rotateAroundAxisGlobalKernel(self.queue, HOST_AxisVectors.shape, None, DEVICE_ErVectors, DEVICE_AxisVectors, DEVICE_PhiValues)
        cl.enqueue_copy(self.queue, HOST_ErVectors, DEVICE_ErVectors)

        GPU_VectorErResults = rfn.structured_to_unstructured(HOST_ErVectors)
        GPU_VectorErResults = np.delete(GPU_VectorErResults, -1, axis=1)

        self.assertTrue(np.allclose(GPU_VectorErResults, CPU_VectorErResults, atol=1e-3))

    def test_whenNormalizeVector_GPU_and_CPU_shouldReturnSameValue(self):
        N = 300
        CPU_VectorEr, HOST_ErVectors, DEVICE_ErVectors = self.makeRandomVectorsAndBuffers(N)

        self.program.normalizeVectorGlobalKernel(self.queue, HOST_ErVectors.shape, None, DEVICE_ErVectors)
        cl.enqueue_copy(self.queue, HOST_ErVectors, DEVICE_ErVectors)

        GPU_VectorErResults = rfn.structured_to_unstructured(HOST_ErVectors)
        GPU_VectorErResults = np.delete(GPU_VectorErResults, -1, axis=1)
        for i, vector in enumerate(CPU_VectorEr):
            vector.normalize()
        CPU_VectorErResults = np.array([[vector.x, vector.y, vector.z] for vector in CPU_VectorEr])

        self.assertTrue(np.all(np.isclose(GPU_VectorErResults, CPU_VectorErResults)))

    @unittest.skip("A visual test, not a unit test")
    def test_whenGeneratingRandomNumberImage_shouldBeNoizyWithoutApparentPatterns(self):
        N = 1000000
        HOST_randomSeed = np.random.randint(low=0, high=2 ** 32 - 1, size=N, dtype=cl.cltypes.uint)
        DEVICE_randomSeed = cl.Buffer(self.ctx, cl.mem_flags.READ_WRITE | cl.mem_flags.COPY_HOST_PTR,
                                      hostbuf=HOST_randomSeed)
        HOST_randomFloat = np.empty(N, dtype=cl.cltypes.float)
        DEVICE_randomFloat = cl.Buffer(self.ctx, cl.mem_flags.READ_WRITE | cl.mem_flags.COPY_HOST_PTR,
                                       hostbuf=HOST_randomFloat)
        self.program.fillRandomFloatBuffer(self.queue, (N,), None, DEVICE_randomSeed, DEVICE_randomFloat)
        cl.enqueue_copy(self.queue, HOST_randomFloat, DEVICE_randomFloat)

        plt.imshow(HOST_randomFloat.reshape((1000, 1000)))
        plt.show()
