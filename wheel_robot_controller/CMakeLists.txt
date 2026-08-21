cmake_minimum_required(VERSION 3.16)
project(wheel_robot_controller)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclpy REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_msgs REQUIRED)

# Diretório de scripts
set(SCRIPTS_DIR "${CMAKE_CURRENT_SOURCE_DIR}/scripts")

# Instalar scripts Python
install(PROGRAMS
  ${SCRIPTS_DIR}/wheel_controller.py
  DESTINATION lib/${PROJECT_NAME}
)

# Instalar diretórios
install(DIRECTORY
  scripts
  DESTINATION share/${PROJECT_NAME}
)

ament_package()