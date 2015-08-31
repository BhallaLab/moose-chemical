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

    def test_multiple(self):
        global args
        #args['model_file'] = '../_models/multiply_reaction.dot'
        #chem2moose.main(args)


if __name__ == '__main__':
    unittest.main()
