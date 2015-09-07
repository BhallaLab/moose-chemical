import unittest
import sys
import gv
import moose.utils as mu
import moose

class Args: pass
args = {
    'solver' : 'moose',
    'plot' : False,
    'outfile' : None,
    'sim_time' : 10,
    'log' : 'debug'
    }

class TestGV( unittest.TestCase ):

    def test_simple(self):
        global args
        args['model_file'] = '_models/simple.dot'
        model = gv.main(args)
        a, b = model.tables['a'], model.tables['b']
        mu.plotRecords(
                { 'a' : a, 'b' : b }
                , outfile = 'simple_test.png'
                )
        real, computed= 1.001, b.vector[-1]
        error = abs((real - computed) / real)
        steady_state = (b.vector[-1] ** 2.0) / a.vector[-1] 
        print("+ Solution: %s, computed: %s, error: %s" % (real, computed, error))
        print("|| Steay state: %s" % steady_state)
        self.assertAlmostEqual(steady_state, 2.0)
        self.assertTrue(error < 0.001)


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    suite = unittest.TestSuite()
    tests = ['test_simple']
    for t in tests[-1:]:
        suite.addTest(TestGV(t))
    runner.run(suite)
