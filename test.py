import unittest
import sys
import chem2moose

class Args: pass
args = {
    'solver' : 'moose',
    'plot' : False,
    'outfile' : None,
    'sim_time' : 30,
    }

class TestGvChem( unittest.TestCase ):

    def test_simple(self):
        global args
        args['model_file'] = '_models/simple.yml'
        tables = chem2moose.main(args)
        a, c = tables['a'], tables['c']
        b = tables['b']
        self.assertAlmostEqual(c.vector[-1], 1.12794913)

    def test_simple_expr(self):
        global args
        args['model_file'] = '_models/simple_expr.yml'
        tables = chem2moose.main(args)
        a, b, c = tables['a'], tables['b'], tables['c']
        print a.vector[-1]
        print c.vector[-1]



if __name__ == '__main__':
    unittest.main()
