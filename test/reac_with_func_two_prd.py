import moose
import pylab

compt = moose.CubeMesh('/compt')
compt.volume = 1e-2

a = moose.Pool('/compt/a')
b = moose.Pool('/compt/b')
c = moose.Pool('/compt/c')

a.concInit = 1.0
b.concInit = 2.0
c.concInit = 0.0

reac = moose.Reac('/reac')

reac.connect('sub', a, 'reac')
reac.connect('sub', b, 'reac')
reac.connect('prd', c, 'reac')
reac.connect('prd', c, 'reac')

tableA = moose.Table2('/tablea')
tableB = moose.Table2('/tableb')
tableC = moose.Table2('/tablec')

tableA.connect('requestOut', a, 'getConc')
tableB.connect('requestOut', b, 'getConc')
tableC.connect('requestOut', c, 'getConc')

ftab = moose.Table2('/tabfunc')

func = moose.Function('/func')
expr = '2.0*x0*x1-0.5*x2'
func.expr = expr
func.x.num = 3
func.mode = 0

moose.connect(ftab, 'requestOut', func, 'getValue')

## Connection function.
moose.connect(a, 'nOut', func.x[0], 'input' )
moose.connect(b, 'nOut', func.x[1], 'input' )
moose.connect(c, 'nOut', func.x[2], 'input' )

moose.connect(func, 'valueOut', a, 'decrement')
moose.connect(func, 'valueOut', b, 'decrement')
moose.connect(func, 'valueOut', c, 'increment')

for i in range(10, 16):
    moose.setClock(i, 5e-5)

moose.reinit()
moose.start(30)

#
#pylab.plot(ftab.vector, label='x\'=%s' % expr)
#pylab.legend(loc='best', framealpha=0.4)
#pylab.show()

ss = (tableA.vector[-1] * tableB.vector[-1]) / (tableC.vector[-1] ** 2.0)
print("Steady state: %s" % ss)

import pylab
pylab.plot(tableA.vector, label = 'a')
pylab.plot(tableB.vector, label = 'b')
pylab.plot(tableC.vector, label = 'c')
pylab.legend(loc='best', framealpha=0.4)
pylab.show()


