#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from mavros_msgs.srv import CommandBool, SetMode, CommandTOL
import math
import time


class EllipseTrajectory(Node):

    def __init__(self):
        super().__init__('ellipse_trajectory_node')

        #Creates a publisher for sending position setpoints to MAVROS
        self.pub = self.create_publisher(
            PoseStamped,
            '/mavros/setpoint_position/local',
            10
        )

        # Creates service clients for arming the vehicle, setting the mode, and taking off
        self.arm_client = self.create_client(
            CommandBool, '/mavros/cmd/arming'
        )
        self.mode_client = self.create_client(
            SetMode, '/mavros/set_mode'
        )
        self.takeoff_client = self.create_client(
            CommandTOL, '/mavros/cmd/takeoff'
        )

        #Ellipse Parameters (in meters)
        self.a = 36.0     # major axis (m)
        self.b = 18.0     # minor axis (m)
        self.z = 10.0     # altitude (m)

        self.theta = 0.0
        self.dtheta = 0.009 
         #Angular speed of the maneuver in rad/s

        self.total_theta = 0.0
        self.max_theta = 2 * math.pi * 3  # Three full ellipses
        self.rtl_sent = False

       
        self.started_ellipse = False
        
        #This sets the publishing rate of the setpoint ot 20 Hz
        self.timer = self.create_timer(0.05, self.timer_cb)  

    #Method to arm the vehicle and set mode to "GUIDED" and takeoff
    def arm_guided_takeoff(self):
        #Displays a message if mavros is not running and waits for the services to be available
        self.get_logger().info('Waiting for MAVROS services...')
        self.arm_client.wait_for_service()
        self.mode_client.wait_for_service()
        self.takeoff_client.wait_for_service()

        # Arm vehicle
        arm_req = CommandBool.Request()
        arm_req.value = True
        self.arm_client.call_async(arm_req)
        time.sleep(2.0)

        # Set GUIDED mode
        mode_req = SetMode.Request()
        mode_req.custom_mode = 'GUIDED'
        self.mode_client.call_async(mode_req)
        time.sleep(2.0)

        # Takeoff to 10m altitude
        takeoff_req = CommandTOL.Request()
        takeoff_req.altitude = self.z
        takeoff_req.latitude = 0.0
        takeoff_req.longitude = 0.0
        takeoff_req.min_pitch = 0.0
        takeoff_req.yaw = 0.0
        self.takeoff_client.call_async(takeoff_req)

        self.get_logger().info(f'Takeoff initiated to {self.z} m')

        # Wait until vehicle is airborne
        time.sleep(8.0)

        self.started_ellipse = True
        self.get_logger().info('Starting elliptical trajectory')

    #Method to publish the position setpoint for the ellipse trajectory
    def timer_cb(self):

        if not self.started_ellipse:
            return

        # After two ellipses → RTL
        if self.total_theta >= self.max_theta:
            if not self.rtl_sent:
                self.get_logger().info('Two ellipses completed. Switching to RTL.')

                rtl_req = SetMode.Request()
                rtl_req.custom_mode = 'RTL'
                self.mode_client.call_async(rtl_req)

                self.rtl_sent = True

            return  # STOP publishing setpoints

        msg = PoseStamped()
        msg.header.stamp = self.get_clock().now().to_msg()

        # Clockwise ellipse
        msg.pose.position.x = self.a * math.cos(self.theta)
        msg.pose.position.y = -self.b * math.sin(self.theta)
        msg.pose.position.z = self.z

        self.pub.publish(msg)

        self.theta += self.dtheta
        self.total_theta += self.dtheta


def main(args=None):
    rclpy.init(args=args)
    node = EllipseTrajectory()

    node.arm_guided_takeoff()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

