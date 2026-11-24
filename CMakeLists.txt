cmake_minimum_required(VERSION 3.8)
project(oomwoo_gazebo_harmonic)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(urdf REQUIRED)

install(DIRECTORY urdf config rviz launch worlds sdf sdf/meshes
  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS
  oomwoo_gazebo_harmonic/bump_recovery.py
  oomwoo_gazebo_harmonic/cliff_detector.py
  DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(test_cliff_detector test/test_cliff_detector.py)
endif()

ament_package()
