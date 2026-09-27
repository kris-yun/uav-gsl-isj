#!/usr/bin/env python3
"""Oracle wind service node using gadentools to read GADEN simulation data."""
import rclpy
from rclpy.node import Node
from gaden_msgs.srv import WindPosition
from gadentools.Simulation import Simulation
import numpy as np

class OracleWindNode(Node):
    def __init__(self):
        super().__init__('oracle_wind_node')
        
        self.declare_parameter('vgr_data_path', '')
        self.declare_parameter('config_id', '2,4-1_fast')
        
        vgr_path = self.get_parameter('vgr_data_path').value
        config_id = self.get_parameter('config_id').value
        
        if not vgr_path:
            self.get_logger().error('vgr_data_path not set!')
            return
        
        wind_path = f"{vgr_path}/wind_simulations/{config_id}"
        occ_path = f"{vgr_path}/OccupancyGrid3D.csv"
        
        self.get_logger().info(f'Loading wind from: {wind_path}')
        self.get_logger().info(f'Loading occupancy from: {occ_path}')
        
        try:
            self.sim = Simulation(wind_path, occ_path)
            self.get_logger().info(f'GADEN loaded. cell_size={self.sim.cell_size}')
            self.get_logger().info(f'env_min={self.sim.env_min}, env_max={self.sim.env_max}')
        except Exception as e:
            self.get_logger().error(f'Failed to load: {e}')
            return
        
        self.srv = self.create_service(WindPosition, '/wind_value', self.wind_callback)
        self.get_logger().info('Oracle wind service ready')
    
    def wind_callback(self, request, response):
        u_list = []
        v_list = []
        w_list = []
        
        for x, y, z in zip(request.x, request.y, request.z):
            try:
                wind = self.sim.getWind(0, float(x), float(y), float(z))
                u_list.append(float(wind[0]))
                v_list.append(float(wind[1]))
                w_list.append(float(wind[2]))
            except Exception as e:
                u_list.append(0.0)
                v_list.append(0.0)
                w_list.append(0.0)
        
        response.u = u_list
        response.v = v_list
        response.w = w_list
        return response

def main():
    rclpy.init()
    node = OracleWindNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
