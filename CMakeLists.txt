cmake_minimum_required(VERSION 3.31)
project(firewatch C)

set(CMAKE_C_STANDARD 23)
add_executable(firewatch main.c)

find_package(libwebsockets CONFIG REQUIRED)

target_link_libraries(firewatch PRIVATE websockets_shared)