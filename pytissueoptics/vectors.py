import numpy as np
import math
import sys
import random
from .vector import Vector
from .scalars import *

"""
Vectors and Scalars are arrays of Vector and scalars (float, int, etc...).
They appear as list of vectors or list of scalar, they are iterable.

These classes are putting in place the structure to act on an array of values, 
possibly in parallel.  Vectors is identical to Vector with its API but it always
acts on an array of [Vector]. A possible implementation would use the GPU to perform
the operations.

This will permit expressive object-oriented code such as:

a = Vectors(N=1000)
b = Vectors(N=1000)

c = a+b

"""


class NativeVectors:
    """ This is the reference implementation of Vectors. Other classes will
    be created such as GPUVectors, NumpyVectors, CuPyVectors, and others to refine the
    implementation for speed. 
    """

    def __init__(self, vectors=None, N=None):
        self.v = []
        if vectors is not None:
            for v in vectors:
                self.v.append(Vector(v))  # always copy
        elif N is not None:
            self.v = [Vector(0, 0, 0)] * N
        self._iteration = 0

    @property
    def count(self):
        return len(self.v)

    @classmethod
    def random(cls, N):
        vectors = []
        for i in range(N):
            x = random.random() * 2 - 1
            y = random.random() * 2 - 1
            z = random.random() * 2 - 1
            vectors.append(Vector(x, y, z))
        return Vectors(vectors)

    @classmethod
    def randomUnitary(cls, N):
        vectors = []
        for i in range(N):
            x = random.random() * 2 - 1
            y = random.random() * 2 - 1
            z = random.random() * 2 - 1
            vectors.append(Vector(x, y, z).normalized())
        return Vectors(vectors)

    @classmethod
    def fromScaledSum(cls, a, b, scale):
        return a.addScaled(b, scale)

    def addScaled(self, rhs, scale):
        return Vectors([v1 + v2 * s for (v1, v2, s) in list(zip(self.v, rhs, scale))])

    @property
    def isUnitary(self) -> [bool]:
        return [v.isUnitary for v in self.v]

    @property
    def isNull(self) -> [bool]:
        return [v.isNull for v in self.v]

    # def __repr__(self):
    #     return "({0:.4f},{1:.4f},{2:.4f})".format(self.x, self.y, self.z)

    # def __str__(self):
    #     return "({0:.4f},{1:.4f},{2:.4f})".format(self.x, self.y, self.z)

    def __len__(self):
        return len(self.v)

    def __mul__(self, scale):
        return Vectors([v1 * s for (v1, s) in list(zip(self.v, scale))])

    def __rmul__(self, scale):
        return Vectors([v1 * s for (v1, s) in list(zip(self.v, scale))])

    def __truediv__(self, scale):
        return Vectors([v1 / s for (v1, s) in list(zip(self.v, scale))])

    def __add__(self, rhs):
        return Vectors([v1 + v2 for (v1, v2) in list(zip(self.v, rhs.v))])

    def __neg__(self):
        return Vectors([-v1 for v1 in self.v])

    def __sub__(self, rhs):
        return Vectors([v1 - v2 for (v1, v2) in list(zip(self.v, rhs.v))])

    def __getitem__(self, index):
        return self.v[index]

    def __setitem__(self, index, newvalue):
        self.v[index] = newvalue

    def __eq__(self, rhs):
        each = [v1.isEqualTo(v2) for (v1, v2) in list(zip(self.v, rhs.v))]
        return np.array(each).all()

    def __iter__(self):
        self._iteration = 0
        return self

    def __next__(self):
        if self._iteration < self.count:
            result = self.v[self._iteration]
            self._iteration += 1
            return result
        else:
            raise StopIteration

    def isEqualTo(self, rhs):
        return Scalars([v1.isEqualTo(v2) for (v1, v2) in list(zip(self.v, rhs))])

    def isAlmostEqualTo(self, rhs, epsilon):
        return Scalars([v1.isAlmostEqualTo(v2, epsilon) for (v1,v2) in list(zip(self.v, rhs))])

    def isParallelTo(self, rhs, epsilon=1e-7):
        return Scalars([v1.isParallelTo(v2) for (v1, v2) in list(zip(self.v, rhs))])

    def anyPerpendicular(self):
        return Vectors([v1.anyPerpendicular() for v1 in self.v])

    def anyUnitaryPerpendicular(self):
        return Vectors([v1.anyUnitaryPerpendicular() for v1 in self.v])

    def isInXYPlane(self, atZ, epsilon=0.001):
        return Scalars([v1.isInXYPlane(atZ=atZ, epsilon=epsilon) for v1 in self.v])

    def isInYZPlane(self, atX, epsilon=0.001):
        return Scalars([v1.isInYZPlane(atX=atX, epsilon=epsilon) for v1 in self.v])

    def isInZXPlane(self, atY, epsilon=0.001):
        return Scalars([v1.isInZXPlane(atY=atY, epsilon=epsilon) for v1 in self.v])

    def isInPlane(self, origin: 'Vector', normal: 'Vector', epsilon=0.001) -> bool:
        return Scalars([v1.isInPlane(origin, normal, epsilon) for v1 in self.v])

    def norm(self):
        return Scalars([v1.norm() for v1 in self.v])

    def abs(self):
        return Scalars([v1.abs() for v1 in self.v])

    def normalize(self):
        [v1.normalize() for v1 in self.v]
        return self

    def normalized(self):
        return Vectors([v1.normalized() for v1 in self.v])

    def isPerpendicularTo(self, rhs, epsilon=1e-7):
        return Scalars([v1.isPerpendicularTo(v2) for (v1, v2) in list(zip(self.v, rhs))])

    def cross(self, rhs):
        return Vectors([v1.cross(v2) for (v1, v2) in list(zip(self.v, rhs))])

    def dot(self, rhs):
        return Scalars([v1.dot(v2) for (v1, v2) in list(zip(self.v, rhs))])

    def normalizedCrossProduct(self, rhs):
        return Vectors([v1.normalizedCrossProduct(v2) 
            for (v1,v2) in list(zip(self.v, rhs))])

    def normalizedDotProduct(self, rhs):
        return Scalars([v1.normalizedDotProduct(v2) for (v1, v2) in list(zip(self.v, rhs))])

    def angleWith(self, v, axis):
        return Scalars([v1.angleWith(v=v2, axis=v3) for (v1, v2, v3) in list(zip(self.v, v, axis))])

    def planeOfIncidence(self, normal):
        return Vectors([v1.planeOfIncidence(normal=v2) for (v1, v2) in list(zip(self.v, normal))])

    def angleOfIncidence(self, normal):
        dotProduct = self.dot(normal)
        correctedNormal = Vectors([n*(1.0 - 2.0 * (s < 0)) for (n, s) in list(zip(normal, dotProduct.v))])

        planeNormal = self.planeOfIncidence(correctedNormal)
        angles = Scalars(self.angleWith(correctedNormal, axis=planeNormal))
        return angles, planeNormal, correctedNormal

    def rotateAround(self, u, theta):
        [v1.rotateAround(v2, t) for (v1, v2, t) in list(zip(self.v, u.v, theta))]
        return self

    def rotatedAround(self, u, theta):
        v = Vectors(self) # copy
        [v1.rotateAround(v2,t) for (v1,v2,t) in list(zip(v.v, u.v, theta))]
        return v


class NumpyVectors:
    """ This is the Reference Vectors Class for numpy-like calculations.
    This architecture will be used by cupy since it is a drop-in replacement
    """

    def __init__(self, vectors=None, N=None):
        if vectors is not None:
            if type(vectors) == np.ndarray:
                self.v = vectors.astype('float64')
            else:
                self.v = np.asarray(vectors, dtype=np.float64)
        elif N is not None:
            self.v = np.zeros(3, N, dtype=np.float64)
            
        self._iteration = 0
    
    def __len__(self):
        return self.v.shape[1]

    def __mul__(self, other):
        if isinstance(other, NumpyVectors):
            return NumpyVectors(np.multiply(self.v, other.v))
        elif isinstance(other, NumpyScalars):
            return NumpyVectors(np.multiply(self.v * other.v[:, None]))
        else:
            return NumpyVectors(np.multiply(self.v, other))

    def __truediv__(self, other):
        if isinstance(other, NumpyVectors):
            return NumpyVectors(np.true_divide(self.v, other.v))
        elif isinstance(other, NumpyScalars):
            return NumpyVectors(np.true_divide(self.v * other.v[:, None]))
        else:
            return NumpyVectors(np.true_divide(self.v, other))

    def __add__(self, other):
        if isinstance(other, NumpyVectors):
            return NumpyVectors(np.add(self.v, other.v))
        else:
            return NumpyVectors(np.add(self.v, other))

    def __sub__(self, other):
        if isinstance(other, NumpyVectors):
            return NumpyVectors(np.subtract(self.v, other.v))
        else:
            return NumpyVectors(np.subtract(self.v, other))

    def __neg__(self):
        return NumpyVectors(np.negative(self.v))

    def __eq__(self, other):
        if isinstance(other, NumpyVectors):
            return NumpyVectors(np.equal(self.v, other.v))
        else:
            return NumpyVectors(np.subtract(self.v, other))

    """ The getitem, setitem, iter, next special methods should not be used
    because never should there be need to bypass the numpy function. Such use
    could and will deteriorate performances and possibly fail to parallelize.
    Can be used to unit test """

    def __getitem__(self, index):
        return self.v[:, index]

    def __setitem__(self, index, value):
        self.v[:, index] = value

    def __iter__(self):
        self._iteration = 0
        return self

    def __next__(self):
        result = self.v[:, self._iteration]
        self._iteration += 1
        return result

    @property
    def isUnitary(self):
        return np.less(np.abs(np.linalg.norm(self.v, axis=0))-1, 1e-9)

    @property
    def isNull(self):
        return np.less(np.linalg.norm(self.v, axis=0), 1e-9)

    @property
    def count(self):
        return len(self.v)

    @classmethod
    def randomUniform(cls, N, r):
        theta = (np.random.rand(1, N) * 2 * np.pi)
        phi = (np.random.rand(1, N) * np.pi)
        x = (r * np.sin(phi) * np.cos(theta))
        y = (r * np.sin(phi) * np.sin(theta))
        z = r * np.cos(phi)
        return NumpyVectors(np.concatenate((x, y, z), axis=0))

    @classmethod
    def randomUniformUnitary(cls, N):
        theta = np.random.rand(1, N) * 2 * np.pi
        phi = np.random.rand(1, N) * np.pi
        x = np.sin(phi)*np.cos(theta)
        y = np.sin(phi)*np.sin(theta)
        z = np.cos(phi)
        return NumpyVectors(np.concatenate((x, y, z), axis=0))

    def isEqualTo(self, other):
        if isinstance(other, NumpyVectors):
            return NumpyScalars(np.less(np.abs(np.subtract(self.v, other.v)), 1e-9))
        else:
            return NumpyScalars(np.less(np.abs(np.subtract(self.v, other)), 1e-9))

    def isAlmostEqualTo(self, other, epsilon):
        if isinstance(other, NumpyVectors):
            return NumpyScalars(np.less(np.abs(np.subtract(self.v, other.v)), epsilon))
        else:
            return NumpyScalars(np.less(np.abs(np.subtract(self.v, other)), epsilon))

    def isParallelTo(self, other, epsilon=1e-9):
        return np.less(self.normalizedDotProduct(other.v) - 1, epsilon)

    def anyPerpendicular(self):
        pass

    def anyUnitaryPerpendicular(self):
        pass

    def isInXYPlane(self, atZ, epsilon=0.001):
        pass

    def isInYZPlane(self, atX, epsilon=0.001):
        pass

    def isInZXPlane(self, atY, epsilon=0.001):
        pass

    def isInPlane(self, origin: 'Vector', normal: 'Vector', epsilon=0.001) -> bool:
        pass

    def norm(self):
        return NumpyScalars(np.linalg.norm(self.v, axis=0))

    def abs(self):
        return NumpyVectors(np.abs(self.v))

    def normalize(self):
        self.v = self.v/np.linalg.norm(self.v, axis=0)

    def normalized(self):
        return NumpyVectors(self.v/np.linalg.norm(self.v, axis=0))

    def isPerpendicularTo(self, other, epsilon=1e-9):
        pass

    def cross(self, other):
        return NumpyVectors(np.cross(self.v, other.v))

    def dot(self, other):
        return NumpyScalars(np.dot(self.v, other.v))

    def normalizedCrossProduct(self, other):
        pass

    def normalizedDotProduct(self, other):
        '''TODO: '''
        productNorm = self.norm() * other.norm()
        if productNorm == 0:
            return 0
        return self.dot(other) * (1 / math.sqrt(productNorm))

    def angleWith(self, v, axis):
        pass

    def planeOfIncidence(self, normal):
        pass

    def angleOfIncidence(self, normal):
        pass

    def rotateAround(self, u, theta):
        pass


Vectors = NativeVectors
