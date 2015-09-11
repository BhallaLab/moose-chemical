CMAKE_MINIMUM_REQUIRED(VERSION 2.8)
PROJECT(camkii)

SET(CMAKE_VERBOSE_MAKEFILE OFF)

# Create directories to install systemc

ADD_DEFINITIONS("-Wall -DDEBUG --std=c++11")
ADD_DEFINITIONS("-DMONITOR")

OPTION(PROFILING "Profile the code" OFF)
IF(PROFILING)
    MESSAGE("++ gprof is enabled")
    SET(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -pg")
    SET(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -pg")
    SET(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} -pg")
ENDIF()

INCLUDE_DIRECTORIES(${SYSTEMC_INSTALL_DIR}/include)

OPTION(ENABLE_TEST "Enable tests" ON)
IF(ENABLE_TEST)
    ADD_DEFINITIONS("-DENABLE_TEST")
ENDIF()

#ADD_SUBDIRECTORY(models)
ADD_EXECUTABLE(camkii main.cc camkii.cc)

# Target Tantrika depends on external project systemc-2.3. Build and install it
# first before continue building Tantrika.
TARGET_LINK_LIBRARIES(camkii systemc m)



