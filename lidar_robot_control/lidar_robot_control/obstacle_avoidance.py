#!/usr/bin/env python3
"""
Obstacle Avoidance Node
- Doc /scan tu LiDAR 2D
- Chia 3 vung: TRAI | TRUOC | PHAI
- Quyet dinh: di thang / quay trai / quay phai / lui
- Publish /cmd_vel
"""
import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist


class ObstacleAvoidance(Node):
    def __init__(self):
        super().__init__('obstacle_avoidance')

        # ===== PARAMETERS =====
        self.declare_parameter('safe_distance', 5.0)      # m
        self.declare_parameter('front_angle_deg', 30.0)   # +/- 30 do
        self.declare_parameter('side_angle_deg', 90.0)    # 30-90 do moi ben
        self.declare_parameter('forward_speed', 10.0)      # m/s
        self.declare_parameter('turn_speed', 0.5)         # rad/s
        self.declare_parameter('backward_speed', 10.0)     # m/s

        self.safe_distance = self.get_parameter('safe_distance').value
        self.front_angle   = math.radians(self.get_parameter('front_angle_deg').value)
        self.side_angle    = math.radians(self.get_parameter('side_angle_deg').value)
        self.forward_speed = self.get_parameter('forward_speed').value
        self.turn_speed    = self.get_parameter('turn_speed').value
        self.backward_speed= self.get_parameter('backward_speed').value

        # ===== ROS =====
        self.sub = self.create_subscription(LaserScan, '/scan', self.scan_callback, 10)
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)

        self.latest_scan = None
        self.last_scan_time = self.get_clock().now()

        self.timer = self.create_timer(0.1, self.control_loop)  # 10 Hz

        self.get_logger().info('Obstacle Avoidance started')
        self.get_logger().info(f'  safe_distance = {self.safe_distance} m')
        self.get_logger().info(f'  front_angle   = +/-{math.degrees(self.front_angle):.0f} deg')
        self.get_logger().info(f'  forward_speed = {self.forward_speed} m/s')
        self.get_logger().info(f'  turn_speed    = {self.turn_speed} rad/s')

    def scan_callback(self, msg):
        self.latest_scan = msg
        self.last_scan_time = self.get_clock().now()

    def get_min_distance(self, ranges, angle_min, angle_increment, angle_lo, angle_hi):
        """Tim khoang cach nho nhat trong vung goc [angle_lo, angle_hi]."""
        n = len(ranges)
        idx_lo = int((angle_lo - angle_min) / angle_increment)
        idx_hi = int((angle_hi - angle_min) / angle_increment)
        idx_lo = max(0, min(n - 1, idx_lo))
        idx_hi = max(0, min(n - 1, idx_hi))

        min_dist = float('inf')
        for i in range(idx_lo, idx_hi + 1):
            r = ranges[i]
            if math.isfinite(r) and r > 0.05:  # bo qua inf, 0
                if r < min_dist:
                    min_dist = r
        return min_dist

    def control_loop(self):
        cmd = Twist()

        # Neu chua co scan hoac scan qua cu -> dung
        if self.latest_scan is None:
            self.get_logger().warn('Chua co /scan', throttle_duration_sec=2.0)
            self.pub.publish(cmd)
            return

        elapsed = (self.get_clock().now() - self.last_scan_time).nanoseconds / 1e9
        if elapsed > 1.0:
            self.get_logger().warn('Scan qua cu > 1s -> dung', throttle_duration_sec=2.0)
            self.pub.publish(cmd)
            return

        scan = self.latest_scan

        # Vung TRUOC: -front_angle den +front_angle
        front_dist = self.get_min_distance(
            scan.ranges, scan.angle_min, scan.angle_increment,
            -self.front_angle, self.front_angle
        )

        # Vung TRAI: front_angle den side_angle
        left_dist = self.get_min_distance(
            scan.ranges, scan.angle_min, scan.angle_increment,
            self.front_angle, self.side_angle
        )

        # Vung PHAI: -side_angle den -front_angle
        right_dist = self.get_min_distance(
            scan.ranges, scan.angle_min, scan.angle_increment,
            -self.side_angle, -self.front_angle
        )

        # In log
        def fmt(x):
            return f'{x:.2f}' if math.isfinite(x) else 'inf'
        self.get_logger().info(
            f'front={fmt(front_dist)} left={fmt(left_dist)} right={fmt(right_dist)}',
            throttle_duration_sec=0.5
        )

        # ===== QUYET DINH =====
        if front_dist > self.safe_distance:
            # Duong thong -> di thang
            cmd.linear.x = self.forward_speed
            cmd.angular.z = 0.0
        else:
            # Co vat can phia truoc -> chon huong tranh
            if left_dist > right_dist and left_dist > 0.35:
                # Quay trai
                cmd.linear.x = 0.05
                cmd.angular.z = self.turn_speed
                self.get_logger().info('-> Quay TRAI', throttle_duration_sec=0.5)
            elif right_dist > left_dist and right_dist > 0.35:
                # Quay phai
                cmd.linear.x = 0.05
                cmd.angular.z = -self.turn_speed
                self.get_logger().info('-> Quay PHAI', throttle_duration_sec=0.5)
            else:
                # Ca 2 ben deu bi chan -> lui
                cmd.linear.x = -self.backward_speed
                cmd.angular.z = self.turn_speed
                self.get_logger().info('-> LUI + Quay', throttle_duration_sec=0.5)

        self.pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleAvoidance()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Dung robot khi thoat
        stop = Twist()
        node.pub.publish(stop)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
        print('\nDa thoat Obstacle Avoidance')


if __name__ == '__main__':
    main()
