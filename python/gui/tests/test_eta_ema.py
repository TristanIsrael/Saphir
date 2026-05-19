import unittest
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
        self.assertEqual(rmn, 0)

    def test_linear_1sec(self):
        estimator = EMAETAEstimator()
        estimator.setup(100)

        i = 0
        while i < 100:
            estimator.update(1.0) # 1 second for each iteration
            rmn = estimator.remaining_time()
            self.assertEqual(rmn, 99-i)
            i += 1

    def test_linear_10sec(self):
        estimator = EMAETAEstimator()
        estimator.setup(100)

        i = 0
        while i < 100:
            estimator.update(10.0) # 10 second for each iteration
            rmn = estimator.remaining_time()
            self.assertEqual(rmn, (99-i)*10)
            i += 1

    def test_not_linear(self):
        estimator = EMAETAEstimator()
        estimator.setup(10)

        # 1st step: 10 seconds
        estimator.update(10)
        rmn = estimator.remaining_time()
        self.assertEqual(rmn, 90)

        # 2d step: 5 seconds
        estimator.update(5)
        rmn = estimator.remaining_time()
        self.assertEqual(rmn, 68)

        # 3d step: 3 seconds
        estimator.update(3)
        rmn = estimator.remaining_time()
        self.assertAlmostEqual(rmn, 48, 0)

        # 4th step: 10 seconds
        estimator.update(10)
        rmn = estimator.remaining_time()
        self.assertAlmostEqual(rmn, 47, 0)

        # Then 1 second each step
        estimator.update(1)
        rmn = estimator.remaining_time()
        self.assertAlmostEqual(rmn, 29, 0)

        estimator.update(1)
        rmn = estimator.remaining_time()
        self.assertAlmostEqual(rmn, 17, 0)

        estimator.update(1)
        rmn = estimator.remaining_time()
        self.assertAlmostEqual(rmn, 10, 0)

        estimator.update(10)
        rmn = estimator.remaining_time()
        self.assertAlmostEqual(rmn, 10.6, 0)

        estimator.update(1)
        rmn = estimator.remaining_time()
        self.assertAlmostEqual(rmn, 4, 0)

        estimator.update(1)
        rmn = estimator.remaining_time()
        self.assertAlmostEqual(rmn, 0, 0)