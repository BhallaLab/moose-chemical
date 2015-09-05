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
        steady_state = c.vector[-1] / ( a.vector[-1] * b.vector[-1])
        print("+ Solution: %s, computed: %s, error: %s" % (real, computed, error))
        print("|| Steay state: %s" % steady_state)
        self.assertTrue(error < 0.0001)

    def test_simple_2c(self):
        global args
        args['model_file'] = '_models/simple_2c.yml'
        moose.delete('/synapse')
        tables = yacml.main(args)
        a, b, c = tables['a'], tables['b'], tables['c']
        real, computed= 1.12311, c.vector[-1]
        error = abs((real - computed) / real)
        mu.plotRecords( 
                { 'a' : a, 'b' : b, 'c' : c }
                , outfile = 'simple_test_2c.png'
                )
        steady_state = c.vector[-1]**2 / (a.vector[-1] * b.vector[-1])
        print("++ Solution: %s, computed: %s, error: %s" % (real, computed, error))
        print("|| Steady state: %s" % steady_state)
        self.assertTrue(error < 0.0001)

    def test_simple_expr(self):
        global args
        args['model_file'] = '_models/simple_expr.yml'
        moose.delete('/synapse')
        tables = yacml.main(args)
        a, b, c = tables['a'], tables['b'], tables['c']
        real, computed= 1.12311, c.vector[-1]
        error = abs((real - computed) / real)
        mu.plotRecords( 
                { 'a' : a, 'b' : b, 'c' : c }
                , outfile = 'simple_test_expr.png'
                )
        steady_state = c.vector[-1]**2 / (a.vector[-1] * b.vector[-1])
        print("++ Solution: %s, computed: %s, error: %s" % (real, computed, error))
        print("|| Steady state: %s" % steady_state)
        self.assertTrue(error < 0.0001)



if __name__ == '__main__':
    unittest.main()
