add_executable(phase5_beamforming main.cpp)
target_link_libraries(phase5_beamforming PRIVATE Eigen3::Eigen)
add_test(NAME phase5_beamforming COMMAND phase5_beamforming)
