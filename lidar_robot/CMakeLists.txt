cmake_minimum_required(VERSION 3.8)
project(lidar_robot)

find_package(ament_cmake REQUIRED)

# Install toàn bộ thư mục chứa URDF, launch, config, world, rviz, mesh
install(
  DIRECTORY urdf launch config worlds rviz
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
