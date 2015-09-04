import unittest
import sys
import yacml
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

class TestGvChem( unittest.TestCase ):

    def test_simple(self):
        global args
        args['model_file'] = '_models/simple.yml'
        tables = yacml.main(args)
        a, b, c = tables['a'], tables['b'], tables['c']
        mu.plotRecords(
                { 'a' : a, 'b' : b, 'c' : c }
                , outfile = 'simple_test.png'
                )
        real, computed= 0.719224, c.vector[-1]
        error = abs((real - computed) / real)
        print("++ Solution: %s, computed: %s, error: %s" % (real, computed, error))
        self.assertTrue((real - computed) / real < 0.0001)

    def test_simple_2c(self):
        global args
        args['model_file'] = '_models/simple_2c.yml'
        tables = yacml.main(args)
        a, b, c = tables['a'], tables['b'], tables['c']
        real, computed= 0.719224, c.vector[-1]
        print("++ Solution: %s, computed: %s, error: %s" % (real, computed, error))
        self.assertTrue((real - computed) / real < 0.0001)



if __name__ == '__main__':
    unittest.main()
