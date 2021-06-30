cmake_minimum_required(VERSION 3.14)
project(cgiserver C)

set(CMAKE_C_STANDARD 99)

set( CMAKE_THREAD_PREFER_PTHREAD 1 )
find_package(Threads)
if (THREADS_FOUND)
    #ms_link_libraries( ${CMAKE_THREAD_LIBS_INIT})
    #target_link_libraries(pthreads)
    set(USE_THREAD 1)
    set(CMAKE_C_FLAGS  -pthread)
endif (THREADS_FOUND)

add_executable(cgiserver cgiserver.c )




