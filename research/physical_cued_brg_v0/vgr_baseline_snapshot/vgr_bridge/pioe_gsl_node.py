"""PIOE-GSL v4 ? ADCF + WDFP support (no CFSI).

Modules:
  - WDFP: intercepts /Anemometer/WindSensor_reading, projects to div-free, republishes
  - ADCF: rolling buffer of (pos, conc, wind), filters concentration for physics consistency
  - Both operate on point readings, not spatial fields

Key difference from v3 (CFSI):
  - ADCF smooths/consistencifies concentration, does NOT amplify
  - WDFP corrects wind direction to be divergence-free, preserves amplitude
  - Neither changes the fundamental gradient structure the backend relies on
"""
import sys, os, time, math
import rclpy
from rclpy.node import Node
from olfaction_msgs.msg import GasSensor, Anemometer
from geometry_msgs.msg import PoseWithCovarianceStamped
import numpy as np

_this_dir = os.path.dirname(os.path.abspath(__file__))
_pioe_dir = os.path.join(_this_dir, 'pioe_modules')
if _pioe_dir not in sys.path:
    sys.path.insert(0, _pioe_dir)
from adcf_module import ADCFProcessor, ADCFConfig, ConcentrationObservation
from wdpf_module import WDFPProcessor, WDFPConfig, WindObservation


class PIOEGSLNodeV4(Node):
    def __init__(self):
        super().__init__('pioe_gsl_node')

        # Parameters
        self.declare_parameter('enable_adcf', False)
        self.declare_parameter('enable_wdfp', False)
        self.declare_parameter('log_file', '/tmp/pioe_gsl_log.txt')
        self.declare_parameter('lambda_phys', 0.05)
        self.declare_parameter('diffusion_coeff', 0.01)
        self.declare_parameter('grid_resolution', 0.25)

        enable_adcf = self.get_parameter('enable_adcf').value
        enable_wdfp = self.get_parameter('enable_wdfp').value
        self.log_file = self.get_parameter('log_file').value
        lambda_phys = self.get_parameter('lambda_phys').value
        diff_coeff = self.get_parameter('diffusion_coeff').value
        grid_res = self.get_parameter('grid_resolution').value

        # ADCF processor
        if enable_adcf:
            self.adcf = ADCFProcessor(ADCFConfig(
                grid_resolution=grid_res,
                diffusion_coeff=diff_coeff,
                lambda_phys=lambda_phys,
                sigma_c=0.2,
                min_amplitude_ratio=0.5,
                max_iter=50,
            ))
        else:
            self.adcf = None

        # WDFP processor
        if enable_wdfp:
            self.wdfp = WDFPProcessor(WDFPConfig(
                grid_resolution=grid_res,
                jacobi_max_iter=100,
                amplitude_preserve_ratio=0.5,
            ))
        else:
            self.wdfp = None

        # State
        self.latest_gas = None
        self.latest_wind = None
        self.latest_pose = None
        self.n_gas_updates = 0
        self.n_wind_updates = 0

        # Rolling buffers (for ADCF)
        self.conc_buf = []
        self.u_buf = []
        self.v_buf = []
        self.pos_buf = []
        self.buf_max = 50  # larger buffer for better ADCF estimation

        # Subscribers
        self.gas_sub = self.create_subscription(
            GasSensor, '/PID/Sensor_reading', self._gas_cb, 1)
        self.wind_sub = self.create_subscription(
            Anemometer, '/Anemometer/WindSensor_reading', self._wind_cb, 1)
        self.pose_sub = self.create_subscription(
            PoseWithCovarianceStamped, '/amcl_pose', self._pose_cb, 10)

        # Publishers (overwrite original topics)
        self.gas_pub = self.create_publisher(GasSensor, '/PID/Sensor_reading', 1)
        self.wind_pub = self.create_publisher(Anemometer, '/Anemometer/WindSensor_reading', 1)

        # Timer
        self.create_timer(0.1, self._process_and_publish)

        self._log(f"PIOE-GSL v4: ADCF={enable_adcf}, WDFP={enable_wdfp}, "
                  f"lambda={lambda_phys}, D={diff_coeff}, dx={grid_res}")

    def _gas_cb(self, msg):
        self.latest_gas = msg

    def _wind_cb(self, msg):
        self.latest_wind = msg

    def _pose_cb(self, msg):
        p = msg.pose.pose.position
        self.latest_pose = np.array([p.x, p.y])

    def _process_and_publish(self):
        if self.latest_gas is None or self.latest_wind is None:
            return

        gas = self.latest_gas
        wind = self.latest_wind
        raw_conc = float(gas.raw)

        # Wind components
        wu = wind.wind_speed * np.cos(wind.wind_direction)
        wv = wind.wind_speed * np.sin(wind.wind_direction)

        pos = self.latest_pose.copy() if self.latest_pose is not None else np.array([0.0, 0.0])

        # Update buffers
        self.conc_buf.append(raw_conc)
        self.u_buf.append(wu)
        self.v_buf.append(wv)
        self.pos_buf.append(pos)

        if len(self.conc_buf) > self.buf_max:
            self.conc_buf = self.conc_buf[-self.buf_max:]
            self.u_buf = self.u_buf[-self.buf_max:]
            self.v_buf = self.v_buf[-self.buf_max:]
            self.pos_buf = self.pos_buf[-self.buf_max:]

        out_conc = raw_conc
        out_u = wu
        out_v = wv

        # ?? ADCF: filter concentration ??
        if self.adcf is not None and len(self.conc_buf) >= 5:
            try:
                # Build observations from buffer
                obs = []
                for i in range(len(self.conc_buf)):
                    obs.append(ConcentrationObservation(
                        x=float(self.pos_buf[i][0]),
                        y=float(self.pos_buf[i][1]),
                        concentration=self.conc_buf[i],
                        u=self.u_buf[i],
                        v=self.v_buf[i],
                        timestamp=float(i),
                    ))

                # Domain bounds from pose history
                xs = [p[0] for p in self.pos_buf]
                ys = [p[1] for p in self.pos_buf]
                margin = 2.0
                domain = (min(xs)-margin, max(xs)+margin, min(ys)-margin, max(ys)+margin)

                result = self.adcf.filter_observations(obs, domain)
                C_filt = result['C_filtered']
                # Use the value at the last observation position
                # Find nearest grid cell to current position
                gx, gy = result['grid_x'], result['grid_y']
                ix = np.argmin(np.abs(gx - pos[0]))
                iy = np.argmin(np.abs(gy - pos[1]))
                filtered_conc = float(C_filt[iy, ix])

                # Apply only if the change is moderate (don't let ADCF create wild swings)
                if raw_conc > 0.001:
                    ratio = filtered_conc / raw_conc
                    ratio = np.clip(ratio, 0.3, 2.0)  # limit change to 0.3x-2x
                    out_conc = raw_conc * ratio
                else:
                    out_conc = raw_conc  # don't touch near-zero readings

                self.n_gas_updates += 1
                if self.n_gas_updates <= 3 or self.n_gas_updates % 50 == 0:
                    self._log(
                        f"ADCF #{self.n_gas_updates}: "
                        f"C_raw={raw_conc:.4f} -> C_filt={out_conc:.4f} "
                        f"residual={float(np.mean(result['residual'])):.6f}"
                    )
            except Exception as e:
                self.get_logger().error(f"ADCF error: {e}")
                out_conc = raw_conc

        # ?? WDFP: correct wind ??
        if self.wdfp is not None and len(self.u_buf) >= 3:
            try:
                # Build wind observations from buffer
                wobs = []
                for i in range(len(self.u_buf)):
                    wobs.append(WindObservation(
                        x=float(self.pos_buf[i][0]),
                        y=float(self.pos_buf[i][1]),
                        u=self.u_buf[i],
                        v=self.v_buf[i],
                    ))

                xs = [p[0] for p in self.pos_buf]
                ys = [p[1] for p in self.pos_buf]
                margin = 2.0
                domain = (min(xs)-margin, max(xs)+margin, min(ys)-margin, max(ys)+margin)

                result = self.wdfp.project(wobs, domain)
                u_corr = result['u_corr']
                v_corr = result['v_corr']

                # Use corrected wind at current position
                gx, gy = result['grid_x'], result['grid_y']
                ix = np.argmin(np.abs(gx - pos[0]))
                iy = np.argmin(np.abs(gy - pos[1]))
                out_u = float(u_corr[iy, ix])
                out_v = float(v_corr[iy, ix])

                # Preserve original amplitude
                orig_mag = math.sqrt(wu**2 + wv**2)
                corr_mag = math.sqrt(out_u**2 + out_v**2)
                if corr_mag > 0.01 and orig_mag > 0.01:
                    scale = orig_mag / corr_mag
                    # Only scale if the ratio is reasonable
                    if 0.3 < scale < 3.0:
                        out_u *= scale
                        out_v *= scale

                self.n_wind_updates += 1
                if self.n_wind_updates <= 3 or self.n_wind_updates % 50 == 0:
                    orig_dir = math.degrees(math.atan2(wv, wu))
                    corr_dir = math.degrees(math.atan2(out_v, out_u))
                    self._log(
                        f"WDFP #{self.n_wind_updates}: "
                        f"wind {math.sqrt(wu**2+wv**2):.3f}m/s@{orig_dir:.0f}deg "
                        f"-> {math.sqrt(out_u**2+out_v**2):.3f}m/s@{corr_dir:.0f}deg"
                    )
            except Exception as e:
                self.get_logger().error(f"WDFP error: {e}")
                out_u, out_v = wu, wv

        # ?? Publish ??
        # Gas (ADCF-filtered)
        gas_out = GasSensor()
        gas_out.header = gas.header
        gas_out.technology = gas.technology
        gas_out.manufacturer = gas.manufacturer
        gas_out.mpn = gas.mpn
        gas_out.raw = out_conc
        gas_out.raw_units = gas.raw_units
        gas_out.raw_air = gas.raw_air
        gas_out.calib_a = gas.calib_a
        gas_out.calib_b = gas.calib_b
        self.gas_pub.publish(gas_out)

        # Wind (WDFP-corrected)
        if self.wdfp is not None:
            wind_out = Anemometer()
            wind_out.header = wind.header
            wind_out.wind_speed = float(math.sqrt(out_u**2 + out_v**2))
            wind_out.wind_direction = float(math.atan2(out_v, out_u))
            self.wind_pub.publish(wind_out)

    def _log(self, msg):
        self.get_logger().info(msg)
        if self.log_file:
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
            except Exception:
                pass


def main(args=None):
    rclpy.init(args=args)
    node = PIOEGSLNodeV4()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
