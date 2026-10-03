#!/usr/bin/env python3
import sys
import termios
import tty
import select
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


HELP = """
===== WASD TELEOP =====
   W : tien
   S : lui
   A : quay trai
   D : quay phai
   SPACE : dung
   +/- : tang/giam toc do
   Q : thoat
========================
"""


class WasdTeleop(Node):
    def __init__(self):
        super().__init__('wasd_teleop')
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)

        self.linear_speed = 0.3      # m/s
        self.angular_speed = 1.0     # rad/s
        self.step = 0.05

        self.cmd = Twist()
        self.timer = self.create_timer(0.1, self.publish_cmd)
        self.get_logger().info('WASD teleop started')

    def publish_cmd(self):
        self.pub.publish(self.cmd)

    def stop(self):
        self.cmd = Twist()

    def forward(self):
        self.cmd = Twist()
        self.cmd.linear.x = self.linear_speed

    def backward(self):
        self.cmd = Twist()
        self.cmd.linear.x = -self.linear_speed

    def turn_left(self):
        self.cmd = Twist()
        self.cmd.angular.z = self.angular_speed

    def turn_right(self):
        self.cmd = Twist()
        self.cmd.angular.z = -self.angular_speed


def read_key(timeout=0.1):
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        rlist, _, _ = select.select([sys.stdin], [], [], timeout)
        if rlist:
            ch = sys.stdin.read(1)
            return ch
        return None
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def main(args=None):
    rclpy.init(args=args)
    node = WasdTeleop()

    print(HELP)

    try:
        while rclpy.ok():
            key = read_key(0.1)
            if key is None:
                rclpy.spin_once(node, timeout_sec=0)
                continue

            k = key.lower()

            if k == 'w':
                node.forward()
            elif k == 's':
                node.backward()
            elif k == 'a':
                node.turn_left()
            elif k == 'd':
                node.turn_right()
            elif key == ' ':
                node.stop()
            elif k == '+':
                node.linear_speed += node.step
                node.angular_speed += node.step
                print(f'[speed] linear={node.linear_speed:.2f}  angular={node.angular_speed:.2f}')
            elif k == '-':
                node.linear_speed = max(0.05, node.linear_speed - node.step)
                node.angular_speed = max(0.1,  node.angular_speed - node.step)
                print(f'[speed] linear={node.linear_speed:.2f}  angular={node.angular_speed:.2f}')
            elif k == 'q':
                break

            rclpy.spin_once(node, timeout_sec=0)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop()
        node.publish_cmd()
        node.destroy_node()
        rclpy.shutdown()
        print('\nThoat WASD teleop')


if __name__ == '__main__':
    main()