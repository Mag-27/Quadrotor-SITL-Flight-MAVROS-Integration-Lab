# Experiment 3: Elliptical Trajectory Tracking over MAVROS

A ROS 2 node that commands an ArduPilot SITL quadcopter through a closed elliptical path using
`PoseStamped` setpoints published over MAVROS, then verifies the tracked path against the
commanded one.

## How it works

`controller.py` arms the vehicle, switches it to `GUIDED` mode, takes off to a fixed altitude, and
then publishes local position setpoints at 20 Hz:

```
x = a * cos(theta)
y = -b * sin(theta)
z = fixed altitude
```

with `a = 36.0 m` (semi-major axis) and `b = 18.0 m` (semi-minor axis), `theta` advancing at
`0.009 rad/s`. The negative sign on the `y` term produces a clockwise loop when viewed from above.
Setpoint publishing stops once `theta` accumulates to `2*pi*3` — three full laps of the ellipse —
at which point the node commands `RTL` and lets the flight controller bring the vehicle home.

## Running it

1. Build the node:
   ```bash
   # place controller.py in ~/ros2_ws/src/ellipse_uav/ellipse_uav/controller.py
   chmod +x ~/ros2_ws/src/ellipse_uav/ellipse_uav/controller.py
   # register it as a console_scripts entry point in setup.py, e.g.
   #   'ellipse_controller = ellipse_uav.controller:main'
   cd ~/ros2_ws
   colcon build --packages-select ellipse_uav --symlink-install
   source install/setup.bash
   ```
2. Launch SITL and MAVROS:
   ```bash
   sim_vehicle.py -v ArduCopter -f quad --console --map --mavproxy-args="--streamrate=18"
   ros2 launch mavros apm.launch fcu_url:=udp://:14550@127.0.0.1:14555
   ```
3. Run the node:
   ```bash
   ros2 run ellipse_uav ellipse_controller
   ```

## Results

`results/trajectory_plot.png` shows the tracked ground path against the commanded setpoints,
reconstructed from the recorded `data/` rosbag.

- The vehicle traced three complete clockwise laps of the ellipse before the node handed off to
  `RTL`, matching the commanded lap count.
- Setpoint tracking showed no significant steady-state error against the commanded sine/cosine
  path.
- The loop closed cleanly at the center of the ellipse (not a focus), consistent with the
  parametric definition used in the controller.
