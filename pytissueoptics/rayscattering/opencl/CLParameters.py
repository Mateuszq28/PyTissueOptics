import numpy as np

from pytissueoptics.rayscattering.opencl.CLProgram import CLProgram


class CLParameters:
    dataPointSize = 16
    photonSize = 64
    seedSize = 4
    materialSize = 32

    def __init__(self, maxLoggerMemory: int = 1e8, workItemAmount: int = 100,
                 photonAmount: int = 1000, loggerGlobalFactor: float = 0.75):
        self._maxLoggerMemory = maxLoggerMemory
        self._workItemAmount = workItemAmount
        self._photonAmount = photonAmount
        self._loggerGlobalFactor = loggerGlobalFactor

    @property
    def workItemAmount(self):
        return np.int32(self._workItemAmount)

    @workItemAmount.setter
    def workItemAmount(self, value: int):
        self._workItemAmount = value

    @property
    def maxLoggerMemory(self):
        return np.int32(self._maxLoggerMemory)

    @maxLoggerMemory.setter
    def maxLoggerMemory(self, value: int):
        self._maxLoggerMemory = value

    @property
    def photonAmount(self):
        return np.int32(self._photonAmount)

    @photonAmount.setter
    def photonAmount(self, value: int):
        if value < self._workItemAmount:
            self._workItemAmount = value
        self._photonAmount = value

    @property
    def maxLoggableInteractions(self):
        return np.int32(self._maxLoggerMemory / self.dataPointSize)

    @maxLoggableInteractions.setter
    def maxLoggableInteractions(self, value):
        self._maxLoggerMemory = np.int32(value * self.dataPointSize)

    @property
    def maxLoggableInteractionsPerWorkItem(self):
        return np.int32((self.maxLoggerMemory / self.dataPointSize) / self._workItemAmount)

    @maxLoggableInteractionsPerWorkItem.setter
    def maxLoggableInteractionsPerWorkItem(self, value):
        self._maxLoggerMemory = np.int32((value * self.dataPointSize) * self._workItemAmount)

    @property
    def photonsPerWorkItem(self):
        return np.int32(np.floor(self._photonAmount / self._workItemAmount))
    
    @photonsPerWorkItem.setter
    def photonsPerWorkItem(self, value: int):
        self._photonAmount = np.int32(value * self._workItemAmount)

    def autoSetParameters(self, program: CLProgram):
        # FIXME: Algorithm here should send a few batches to check the average interaction per photon
        # then decide the logger size and the photon amount that fills the logger
        # then try a few workItemAmount parameters for speed.
        self._maxLoggerMemory = np.int32(self._loggerGlobalFactor * program.global_memory_size)
