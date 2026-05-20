import unittest
import math
from Saphir import EMAETAEstimator

class TestEtaEma(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_init(self):
        estimator = EMAETAEstimator()
        estimator.setup(100)

        rmn = estimator.remaining_time()
        self.assertEqual(rmn, math.inf)

    def test_linear_1sec(self):
        estimator = EMAETAEstimator()
        estimator.setup(100)

        i = 0
        while i < 10:
            estimator.update(1.0, 10) # 1 second and 10 bytes for each iteration
            rmn = estimator.remaining_time()
            self.assertAlmostEqual(rmn, 9-i, 0)
            i += 1

    def test_linear_10sec(self):
        estimator = EMAETAEstimator()
        estimator.setup(100)

        i = 0
        while i < 10:
            estimator.update(10.0, 10) # 10 seconds and 10 bytes for each iteration
            rmn = estimator.remaining_time()
            self.assertEqual(rmn, 90-(i*10))
            i += 1

    def test_not_linear_time_linear_size(self):
        estimator = EMAETAEstimator()
        estimator.setup(100)

        # 1st step: 10 seconds
        estimator.update(10, 10)
        rmn = estimator.remaining_time()
        self.assertEqual(rmn, 90)

        # 2d step: 5 seconds
        estimator.update(5, 10)
        rmn = estimator.remaining_time()
        self.assertAlmostEqual(rmn, 53.3, 0)

        # 3d step: 3 seconds
        estimator.update(3, 10)
        rmn = estimator.remaining_time()
        self.assertAlmostEqual(rmn, 33.1, 0)

        # 4th step: 10 seconds
        estimator.update(10, 10)
        rmn = estimator.remaining_time()
        self.assertAlmostEqual(rmn, 32.7, 0)

        # Then 1 second each step
        estimator.update(1, 10)
        rmn = estimator.remaining_time()
        self.assertAlmostEqual(rmn, 14.42, 0)

        estimator.update(1, 10)
        rmn = estimator.remaining_time()
        self.assertAlmostEqual(rmn, 8.78, 0)

        estimator.update(1, 10)
        rmn = estimator.remaining_time()
        self.assertAlmostEqual(rmn, 5.625, 0)

        estimator.update(10, 10)
        rmn = estimator.remaining_time()
        self.assertAlmostEqual(rmn, 4, 0)

        estimator.update(1, 10)
        rmn = estimator.remaining_time()
        self.assertAlmostEqual(rmn, 1.5, 0)

        estimator.update(1, 10)
        rmn = estimator.remaining_time()
        self.assertAlmostEqual(rmn, 0, 0)

    def test_fractions(self):
        # Test the ETA with a fraction of a minute

        estimator = EMAETAEstimator()
        estimator.setup(10)

        # 1/10 of seconds for each, which means 1 seconds for all
        estimator.update(0.1, 1)
        rmn = estimator.remaining_time()
        self.assertEqual(rmn, 0.9)

        estimator.update(0.1, 1)
        rmn = estimator.remaining_time()
        self.assertAlmostEqual(rmn, 0.8, 0)

        estimator.update(0.1, 1)
        rmn = estimator.remaining_time()
        self.assertAlmostEqual(rmn, 0.7)

        estimator.update(0.1, 1)
        rmn = estimator.remaining_time()
        self.assertAlmostEqual(rmn, 0.6)

        estimator.update(0.1, 1)
        rmn = estimator.remaining_time()
        self.assertAlmostEqual(rmn, 0.5)

        estimator.update(0.1, 1)
        rmn = estimator.remaining_time()
        self.assertAlmostEqual(rmn, 0.4)

        estimator.update(0.1, 1)
        rmn = estimator.remaining_time()
        self.assertAlmostEqual(rmn, 0.3)

        estimator.update(0.1, 1)
        rmn = estimator.remaining_time()
        self.assertAlmostEqual(rmn, 0.2)

        estimator.update(0.1, 1)
        rmn = estimator.remaining_time()
        self.assertAlmostEqual(rmn, 0.1)