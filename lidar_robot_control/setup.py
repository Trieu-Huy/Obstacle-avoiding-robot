from setuptools import find_packages, setup

package_name = 'lidar_robot_control'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='huy',
    maintainer_email='huy@todo.todo',
    description='Dieu khien robot bang WASD',
    license='MIT',
    entry_points={
        'console_scripts': [
            'wasd_teleop = lidar_robot_control.wasd_teleop:main',
            'wasd_teleop_global = lidar_robot_control.wasd_teleop_global:main',
        ],
    },
)