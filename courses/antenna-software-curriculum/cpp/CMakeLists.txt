cmake_minimum_required(VERSION 3.16)
project(antenna_curriculum CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
add_compile_options(-Wall -Wextra)

# Optional dependencies — targets that need them are skipped if absent.
find_package(Eigen3 3.3 QUIET)
find_package(PkgConfig QUIET)
if(PkgConfig_FOUND)
  pkg_check_modules(FFTW3F IMPORTED_TARGET fftw3f)
endif()

enable_testing()

add_subdirectory(phase1_dsp)
add_subdirectory(phase2_modulation)
add_subdirectory(phase3_coding)

if(Eigen3_FOUND)
  add_subdirectory(phase5_beamforming)
else()
  message(STATUS "Eigen3 not found — skipping phase5_beamforming (apt install libeigen3-dev)")
endif()
