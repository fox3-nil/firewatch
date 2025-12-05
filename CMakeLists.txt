cmake_minimum_required(VERSION 3.10)
project(firewatch C)
set(CMAKE_C_STANDARD 23)
find_package(nng CONFIG REQUIRED)
add_executable(firewatch main.c)

target_link_libraries(firewatch PRIVATE nng::nng)