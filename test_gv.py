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


def load_model(model_path, **kwargs):
    global args
    args['model_file'] = model_path
    model = gv.main(args)
    mu.saveRecords(model.tables, title=model_path, outfile = '%s.dat' % model_path)
    for k in model.tables:
        print("|- %s[-1] = %s" % (k, model.tables[k].vector[-1]))
    return model.tables

class TestGV( unittest.TestCase ):

    def test_simple_a_b_b(self):
        global args
        tables = load_model('_models/simple_a_b_b.dot')
        a, b = tables['a'], tables['b']
        real, computed= 1.001, b.vector[-1]
        error = abs((real - computed) / real)
        steady_state = (b.vector[-1] ** 2.0) / a.vector[-1] 
        print("+ Solution: %s, computed: %s, error: %s" % (real, computed, error))
        print("|| Steay state: %s" % steady_state)
        self.assertAlmostEqual(steady_state, 2.0)
        self.assertTrue(error < 0.001)

    def test_simple_a_a_b(self):
        global args
        try: moose.delete('/model')
        except: pass
        tables = load_model('_models/simple_a_a_b.dot')
        a, b = tables['a'], tables['b']
        real, computed= 0.3069, b.vector[-1]
        error = abs((real - computed) / real)
        steady_state = b.vector[-1] / (a.vector[-1] ** 2.0)
        print("+ Solution: %s, computed: %s, error: %s" % (real, computed, error))
        print("|| Steay state: %s" % steady_state)
        self.assertAlmostEqual(steady_state, 2.0)
        self.assertTrue(error < 0.001)

    def test_simple_a_a_b_b(self):
        global args
        try: moose.delete('/model')
        except: pass
        tables = load_model('_models/simple_a_a_b_b.dot')
        a, b = tables['a'], tables['b']
        real, computed= 0.3069, b.vector[-1]
        error = abs((real - computed) / real)
        steady_state = b.vector[-1] ** 2.0 / (a.vector[-1] ** 2.0)
        print("+ Solution: %s, computed: %s, error: %s" % (real, computed, error))
        print("|| Steay state: %s" % steady_state)
        self.assertAlmostEqual(steady_state, 2.0)
        self.assertTrue(error < 0.001)
 

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    suite = unittest.TestSuite()
    tests = ['test_simple_a_b_b', 'test_simple_a_a_b']
    tests += [ 'test_simple_a_a_b_b' ]
    for t in tests: suite.addTest(TestGV(t))
    runner.run(suite)
