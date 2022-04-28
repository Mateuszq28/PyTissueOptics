import unittest

from mockito import mock, verify, when

from pytissueoptics.scene import Cuboid
from pytissueoptics.scene.scene import Scene
from pytissueoptics.scene.geometry import Vector, BoundingBox, Environment
from pytissueoptics.scene.solids import Solid


class TestScene(unittest.TestCase):
    WORLD_MATERIAL = "worldMaterial"

    def setUp(self):
        self.scene = Scene(worldMaterial=self.WORLD_MATERIAL)

    def testWhenAddingASolidAtAPosition_shouldPlaceTheSolidAtTheDesiredPosition(self):
        SOLID_POSITION = Vector(4, 0, 1)
        SOLID = self.makeSolidWith()
        when(SOLID).translateTo(...).thenReturn()

        self.scene.add(SOLID, position=SOLID_POSITION)

        verify(SOLID).translateTo(SOLID_POSITION)

    def testWhenAddingASolidAtNoSpecificPosition_shouldKeepTheSolidAtItsPredefinedPosition(self):
        SOLID = self.makeSolidWith()
        self.scene.add(SOLID)
        verify(SOLID, times=0).translateTo(...)

    def testWhenAddingASolidThatPartlyOverlapsWithAnotherOne_shouldNotAdd(self):
        OTHER_SOLID = self.makeSolidWith(BoundingBox([2, 5], [2, 5], [2, 5]))
        SOLID = self.makeSolidWith(BoundingBox([0, 3], [0, 3], [0, 3]))
        self.scene.add(OTHER_SOLID)

        with self.assertRaises(Exception):
            self.scene.add(SOLID)

    def testWhenAddingASolidInsideAnotherOne_shouldUpdateOutsideMaterialOfThisSolid(self):
        OUTSIDE_SOLID = self.makeSolidWith(BoundingBox([0, 5], [0, 5], [0, 5]), contains=True)
        SOLID = self.makeSolidWith(BoundingBox([1, 3], [1, 3], [1, 3]))
        OUTSIDE_SOLID_ENV = Environment("A material")
        when(OUTSIDE_SOLID).getEnvironment().thenReturn(OUTSIDE_SOLID_ENV)
        self.scene.add(OUTSIDE_SOLID)

        self.scene.add(SOLID)

        verify(SOLID).setOutsideEnvironment(OUTSIDE_SOLID_ENV)

    def testWhenAddingASolidOverAnotherOne_shouldUpdateOutsideMaterialOfTheOtherSolid(self):
        INSIDE_SOLID = self.makeSolidWith(BoundingBox([0, 5], [0, 5], [0, 5]))
        self.scene.add(INSIDE_SOLID)

        SOLID = self.makeSolidWith(BoundingBox([-1, 6], [-1, 6], [-1, 6]), contains=True)
        SOLID_ENV = Environment("A material")
        when(SOLID).getEnvironment().thenReturn(SOLID_ENV)

        self.scene.add(SOLID)

        verify(INSIDE_SOLID).setOutsideEnvironment(SOLID_ENV)

    def testWhenAddingASolidInsideMultipleOtherSolids_shouldUpdateOutsideMaterialOfThisSolid(self):
        OUTSIDE_SOLID = self.makeSolidWith(BoundingBox([1, 4], [1, 4], [1, 4]))
        OUTSIDE_SOLID_ENV = Environment("A material")
        when(OUTSIDE_SOLID).getEnvironment().thenReturn(OUTSIDE_SOLID_ENV)
        self.scene.add(OUTSIDE_SOLID)

        TOPMOST_OUTSIDE_SOLID = self.makeSolidWith(BoundingBox([0, 5], [0, 5], [0, 5]), contains=True)
        self.scene.add(TOPMOST_OUTSIDE_SOLID)

        SOLID = self.makeSolidWith(BoundingBox([2, 3], [2, 3], [2, 3]))
        when(OUTSIDE_SOLID).contains(...).thenReturn(True)

        self.scene.add(SOLID)

        verify(SOLID).setOutsideEnvironment(OUTSIDE_SOLID_ENV)

    def testWhenAddingASolidOverMultipleOtherSolids_shouldUpdateOutsideMaterialOfTheTopMostSolid(self):
        TOPMOST_INSIDE_SOLID = self.makeSolidWith(BoundingBox([0, 5], [0, 5], [0, 5]), contains=True)
        self.scene.add(TOPMOST_INSIDE_SOLID)

        INSIDE_SOLID = self.makeSolidWith(BoundingBox([1, 4], [1, 4], [1, 4]))
        self.scene.add(INSIDE_SOLID)

        SOLID = self.makeSolidWith(BoundingBox([-1, 6], [-1, 6], [-1, 6]), contains=True)
        SOLID_MATERIAL = "A material"
        when(SOLID).getEnvironment().thenReturn(SOLID_MATERIAL)

        self.scene.add(SOLID)

        verify(TOPMOST_INSIDE_SOLID).setOutsideEnvironment(SOLID_MATERIAL)

    def testWhenAddingASolidThatFitsInsideOneButAlsoContainsOne_shouldUpdateOutsideMaterialOfThisSolidAndTheOneInside(self):
        INSIDE_SOLID = self.makeSolidWith(BoundingBox([2, 3], [2, 3], [2, 3]))
        self.scene.add(INSIDE_SOLID)

        OUTSIDE_SOLID = self.makeSolidWith(BoundingBox([0, 5], [0, 5], [0, 5]), contains=True)
        OUTSIDE_SOLID_ENV = Environment("Outside material")
        when(OUTSIDE_SOLID).getEnvironment().thenReturn(OUTSIDE_SOLID_ENV)
        self.scene.add(OUTSIDE_SOLID)

        SOLID = self.makeSolidWith(BoundingBox([1, 4], [1, 4], [1, 4]))
        SOLID_ENV = Environment("Inside material")
        when(SOLID).getEnvironment().thenReturn(SOLID_ENV)
        when(SOLID).contains(...).thenReturn(False).thenReturn(True)

        self.scene.add(SOLID)

        verify(SOLID).setOutsideEnvironment(OUTSIDE_SOLID_ENV)
        verify(INSIDE_SOLID).setOutsideEnvironment(SOLID_ENV)

    def testWhenAddingASolidInsideASolidStack_shouldRaiseNotImplementedError(self):
        CUBOID_STACK = self.makeSolidWith(BoundingBox([1, 4], [1, 4], [1, 4]), contains=True, isStack=True)
        self.scene.add(CUBOID_STACK)

        INSIDE_SOLID = self.makeSolidWith(BoundingBox([2, 3], [2, 3], [2, 3]))

        with self.assertRaises(NotImplementedError):
            self.scene.add(INSIDE_SOLID)

    def testGivenASceneThatIgnoresIntersections_whenAddingASolidThatPartlyMergesWithAnotherOne_shouldAddTheSolid(self):
        scene = Scene(ignoreIntersections=True)
        OTHER_SOLID = self.makeSolidWith(BoundingBox([2, 5], [2, 5], [2, 5]))
        SOLID = self.makeSolidWith(BoundingBox([0, 3], [0, 3], [0, 3]))
        scene.add(OTHER_SOLID)

        scene.add(SOLID)

    def testWhenGetBoundingBox_shouldReturnABoundingBoxThatExtendsToAllItsSolids(self):
        scene = Scene()
        SOLID1 = self.makeSolidWith(BoundingBox([-5, -3], [-4, -2], [-3, -1]))
        SOLID2 = self.makeSolidWith(BoundingBox([0, 3], [0, 2], [0, 1]))
        scene.add(SOLID1)
        scene.add(SOLID2)

        bbox = scene.getBoundingBox()

        self.assertEqual([-5, 3], bbox.xLim)
        self.assertEqual([-4, 2], bbox.yLim)
        self.assertEqual([-3, 1], bbox.zLim)

    def testGivenNoSolids_whenGetBoundingBox_shouldReturnNone(self):
        scene = Scene()
        self.assertIsNone(scene.getBoundingBox())

    def testWhenAddingASolidWithExistingLabel_shouldRelabelToAUniqueLabel(self):
        solid1 = self.makeSolidWith()
        solid2 = self.makeSolidWith()

        Scene([solid1, solid2], ignoreIntersections=True)

        verify(solid1, times=0).setLabel(...)
        verify(solid2).setLabel("solid_0")

    def testWhenResetOutsideMaterial_shouldSetOutsideMaterialOfAllTheSolidsThatAreNotContained(self):
        INSIDE_SOLID = self.makeSolidWith(BoundingBox([1, 4], [1, 4], [1, 4]), name="InsideSolid")
        self.scene.add(INSIDE_SOLID)
        SOLID = self.makeSolidWith(BoundingBox([-1, 6], [-1, 6], [-1, 6]), contains=True, name="solid")
        self.scene.add(SOLID)

        self.scene.resetOutsideMaterial()

        verify(SOLID, times=1).setOutsideEnvironment(Environment(self.WORLD_MATERIAL))
        verify(INSIDE_SOLID, times=0).setOutsideEnvironment(Environment(self.WORLD_MATERIAL))

    def testWhenCreatingSceneFromSolids_shouldAutomaticallyResetOutsideMaterialOfAllSolidsThatAreNotContained(self):
        INSIDE_SOLID = self.makeSolidWith(BoundingBox([1, 4], [1, 4], [1, 4]), name="InsideSolid")
        SOLID = self.makeSolidWith(BoundingBox([-1, 6], [-1, 6], [-1, 6]), contains=True, name="solid")

        Scene([SOLID, INSIDE_SOLID], worldMaterial=self.WORLD_MATERIAL)

        verify(SOLID, times=1).setOutsideEnvironment(Environment(self.WORLD_MATERIAL))
        verify(INSIDE_SOLID, times=0).setOutsideEnvironment(Environment(self.WORLD_MATERIAL))

    def testWhenGetEnvironmentWithPositionContainedInASolid_shouldReturnEnvironmentOfThisSolid(self):
        SOLID = self.makeSolidWith(BoundingBox([1, 4], [1, 4], [1, 4]), contains=True)
        self.scene.add(SOLID)

        env = self.scene.getEnvironmentAt(Vector(2, 2, 2))

        self.assertEqual(SOLID.getEnvironment(), env)

    def testWhenGetEnvironmentWithPositionOutsideAllSolids_shouldReturnWorldEnvironment(self):
        SOLID = self.makeSolidWith(BoundingBox([1, 4], [1, 4], [1, 4]))
        self.scene.add(SOLID)

        env = self.scene.getEnvironmentAt(Vector(0, 0, 0))

        self.assertEqual(self.scene.getWorldEnvironment(), env)

    def testWhenGetEnvironmentWithPositionContainedInAStack_shouldReturnEnvironmentOfProperStackLayer(self):
        frontLayer = Cuboid(1, 1, 1, material="frontMaterial")
        middleLayer = Cuboid(1, 1, 1, material="middleMaterial")
        backLayer = Cuboid(1, 1, 1, material="backMaterial")
        stack = backLayer.stack(middleLayer, 'front').stack(frontLayer, 'front')
        self.scene.add(stack, position=Vector(0, 0, 0))

        frontEnv = self.scene.getEnvironmentAt(Vector(0, 0, -1))
        middleEnv = self.scene.getEnvironmentAt(Vector(0, 0, 0))
        backEnv = self.scene.getEnvironmentAt(Vector(0, 0, 1))

        self.assertEqual(Environment("frontMaterial", frontLayer), frontEnv)
        self.assertEqual(Environment("middleMaterial", middleLayer), middleEnv)
        self.assertEqual(Environment("backMaterial", backLayer), backEnv)

    @staticmethod
    def makeSolidWith(bbox: BoundingBox = None, contains=False, isStack=False, name="solid"):
        solid = mock(Solid)
        when(solid).getLabel().thenReturn(name)
        when(solid).setLabel(...).thenReturn()
        when(solid).getBoundingBox().thenReturn(bbox)
        when(solid).isStack().thenReturn(isStack)
        when(solid).getVertices().thenReturn([])
        when(solid).setOutsideEnvironment(...).thenReturn()
        when(solid).getEnvironment().thenReturn(Environment("A material"))
        when(solid).getVertices().thenReturn([])
        when(solid).contains(...).thenReturn(contains)
        return solid
