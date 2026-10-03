#!/usr/bin/env python3
import sys
import threading
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import evdev
from evdev import ecodes


HELP = """
===== WASD TELEOP (GLOBAL) =====
   W : tien
   S : lui
   A : quay trai
   D : quay phai
   SPACE : dung
   +/- : tang/giam toc do
   Q : thoat
=================================
"""


class WasdTeleopGlobal(Node):
    def __init__(self, keyboard_path):
        super().__init__('wasd_teleop_global')
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)

        self.linear_speed = 0.3
        self.angular_speed = 1.0
        self.step = 0.05

        self.cmd = Twist()
        self.running = True

        self.keyboard = evdev.InputDevice(keyboard_path)
        self.get_logger().info(f'Keyboard: {self.keyboard.name} ({keyboard_path})')

        self.key_thread = threading.Thread(target=self.read_keys, daemon=True)
        self.key_thread.start()

        self.timer = self.create_timer(0.05, self.publish_cmd)

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

    def read_keys(self):
        for event in self.keyboard.read_loop():
            if not self.running:
                break
            if event.type != ecodes.EV_KEY:
                continue

            key_event = evdev.categorize(event)
            if key_event.keystate != key_event.key_down:
                continue

            code = key_event.keycode

            if code == 'KEY_W':
                self.forward()
                print('[W] forward')
            elif code == 'KEY_S':
                self.backward()
                print('[S] backward')
            elif code == 'KEY_A':
                self.turn_left()
                print('[A] turn left')
            elif code == 'KEY_D':
                self.turn_right()
                print('[D] turn right')
            elif code == 'KEY_SPACE':
                self.stop()
                print('[SPACE] stop')
            elif code in ('KEY_KPPLUS', 'KEY_EQUAL'):
                self.linear_speed += self.step
                self.angular_speed += self.step
                print(f'[speed] linear={self.linear_speed:.2f} angular={self.angular_speed:.2f}')
            elif code == 'KEY_MINUS':
                self.linear_speed = max(0.05, self.linear_speed - self.step)
                self.angular_speed = max(0.1, self.angular_speed - self.step)
                print(f'[speed] linear={self.linear_speed:.2f} angular={self.angular_speed:.2f}')
            elif code == 'KEY_Q':
                print('[Q] quit')
                self.running = False
                rclpy.shutdown()
                break


def main(args=None):
    rclpy.init(args=args)

    if len(sys.argv) > 1:
        keyboard_path = sys.argv[1]
    else:
        keyboards = []
        for path in evdev.list_devices():
            try:
                dev = evdev.InputDevice(path)
                if 'keyboard' in dev.name.lower():
                    keyboards.append(path)
            except Exception:
                pass
        if not keyboards:
            print('Khong tim thay keyboard. Truyen duong dan thu cong:')
            print('  ros2 run lidar_robot_control wasd_teleop_global /dev/input/event3')
            sys.exit(1)
        keyboard_path = keyboards[0]
        print(f'Tu dong chon: {keyboard_path}')

    node = WasdTeleopGlobal(keyboard_path)
    print(HELP)

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.running = False
        node.stop()
        node.publish_cmd()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
        print('\nThoat WASD teleop')


if __name__ == '__main__':
    main()