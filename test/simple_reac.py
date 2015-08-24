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
reac.Kf = 4.0
reac.Kb = 0.2

tableA = moose.Table2('/tablea')
tableB = moose.Table2('/tableb')
tableA.connect('requestOut', a, 'getConc')
tableB.connect('requestOut', b, 'getConc')

moose.reinit()
moose.start(20)

import pylab
pylab.plot(tableA.vector, label = 'a')
pylab.plot(tableB.vector, label = 'b')
pylab.show()

print tableA.vector[-1]/ tableB.vector[-1]

