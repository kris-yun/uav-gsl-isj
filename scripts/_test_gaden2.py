from gadentools.Simulation import Simulation
s = Simulation('/tmp/gaden_wind/House01', '/tmp/gaden_wind/House01/OccupancyGrid3D.csv')
w = s.getWind(0, -5.0, -5.0, 1.0)
print(f'Wind at (-5,-5,1): u={w[0]:.4f}, v={w[1]:.4f}, wz={w[2]:.4f}')
w2 = s.getWind(0, -0.4, -2.9, 1.0)
print(f'Wind at source: u={w2[0]:.4f}, v={w2[1]:.4f}, wz={w2[2]:.4f}')
import math
speed = math.sqrt(w[0]**2 + w[1]**2)
print(f'Wind speed at start: {speed:.4f} m/s')
speed2 = math.sqrt(w2[0]**2 + w2[1]**2)
print(f'Wind speed at source: {speed2:.4f} m/s')
