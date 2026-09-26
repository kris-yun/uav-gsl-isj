#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from gaden_msgs.srv import WindPosition
import numpy as np
import os, csv

class WindValueServer(Node):
    def __init__(self):
        super().__init__('wind_value_server')
        self.declare_parameter('vgr_data_path', '')
        self.declare_parameter('config_id', '2,4-1_fast')
        vgr_path = self.get_parameter('vgr_data_path').value
        config_id = self.get_parameter('config_id').value
        self.wind_data = {}
        wind_dir = os.path.join(vgr_path, 'wind_simulations', config_id)
        if os.path.exists(wind_dir):
            for fname in sorted(os.listdir(wind_dir)):
                if not fname.endswith('.csv') or '_U' in fname or '_V' in fname or '_W' in fname:
                    continue
                import re
                match = re.search(r'_(\d+)\.csv$', fname)
                if not match:
                    continue
                iteration = int(match.group(1))
                positions, vectors = [], []
                with open(os.path.join(wind_dir, fname), 'r') as f:
                    reader = csv.reader(f)
                    next(reader)
                    for row in reader:
                        if len(row) >= 6:
                            vectors.append([float(row[0]), float(row[1]), float(row[2])])
                            positions.append([float(row[3]), float(row[4]), float(row[5])])
                self.wind_data[iteration] = {'pos': np.array(positions), 'vec': np.array(vectors)}
        self.get_logger().info(f'Loaded {len(self.wind_data)} wind iterations from {wind_dir}')
        self.srv = self.create_service(WindPosition, '/wind_value', self.callback)
        self.get_logger().info('wind_value service ready')

    def callback(self, req, res):
        if not self.wind_data:
            for _ in req.x:
                res.u.append(0.0); res.v.append(0.0); res.w.append(0.0)
            return res
        iteration = min(self.wind_data.keys())
        wd = self.wind_data[iteration]
        pos, vec = wd['pos'], wd['vec']
        for i in range(len(req.x)):
            query = np.array([req.x[i], req.y[i], req.z[i]])
            dists = np.linalg.norm(pos - query[np.newaxis, :], axis=1)
            idx = np.argmin(dists)
            res.u.append(float(vec[idx][0]))
            res.v.append(float(vec[idx][1]))
            res.w.append(float(vec[idx][2]))
        return res

def main():
    rclpy.init()
    node = WindValueServer()
    rclpy.spin(node)

if __name__ == '__main__':
    main()
