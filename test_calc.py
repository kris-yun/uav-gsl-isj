import math, sys
a,b,c,d = [float(x) for x in sys.argv[1:5]]
r = math.sqrt((a-c)**2+(b-d)**2)
print((chr(37)+chr(46)+chr(51)+chr(102))%r)
