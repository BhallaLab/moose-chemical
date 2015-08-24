import moose
compt = moose.CubeMesh('/compt')
compt.volume = 1

a = moose.Pool('/compt/a')
b = moose.Pool('/compt/b')
a.concInit = 1.0
b.concInit = 0.0

reac = moose.Reac('/reac')
reac.connect('sub', a, 'reac')
reac.connect('prd', b, 'reac')
#reac.Kf = 4.0
#reac.Kb = 0.2

tableA = moose.Table2('/tablea')
tableB = moose.Table2('/tableb')
tableA.connect('requestOut', a, 'getConc')
tableB.connect('requestOut', b, 'getConc')

func = moose.Function('/func')
func.expr = '1*x0 - 2*x1'
func.x.num = 2
func.mode = 0
#moose.connect(func.x[0], 'input', a, 'getN')
moose.connect(a, 'nOut', func.x[0], 'input')
moose.connect(b, 'nOut', func.x[1], 'input')
#moose.connect(func.x[1], 'input', b, 'getN')
moose.connect(func, 'valueOut', a, 'decrement')
moose.connect(func, 'valueOut', b, 'increment')

moose.reinit()
moose.start(20)

import pylab
pylab.plot(tableA.vector, label = 'a')
pylab.plot(tableB.vector, label = 'b')
pylab.legend(loc='best', framealpha=0.4)
pylab.show()

