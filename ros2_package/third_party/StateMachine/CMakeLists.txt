cmake_minimum_required(VERSION 3.10)
project(StateMachines)
set(CMAKE_CXX_FLAGS "-w -std=c++11 -O3 -g ${CMAKE_CXX_FLAGS}")

include_directories(
    include
)

add_executable(Test test.cpp) 