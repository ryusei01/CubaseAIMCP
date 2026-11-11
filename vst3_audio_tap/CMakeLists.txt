cmake_minimum_required(VERSION 3.25.0)

project(CubaseAiAudioTap
    VERSION 1.0.0.0
    DESCRIPTION "Cubase AI Advisor Audio Tap VST3"
)

set(vst3sdk_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../third_party/vst3sdk" CACHE PATH "Path to VST3 SDK")

if(NOT EXISTS "${vst3sdk_SOURCE_DIR}/CMakeLists.txt")
    message(FATAL_ERROR "VST3 SDK not found at ${vst3sdk_SOURCE_DIR}")
endif()

set(SMTG_ENABLE_VST3_HOSTING_EXAMPLES OFF CACHE BOOL "" FORCE)
set(SMTG_ENABLE_VST3_PLUGIN_EXAMPLES OFF CACHE BOOL "" FORCE)
set(SMTG_ENABLE_VSTGUI_SUPPORT OFF CACHE BOOL "" FORCE)

add_subdirectory(${vst3sdk_SOURCE_DIR} ${PROJECT_BINARY_DIR}/vst3sdk)
smtg_enable_vst3_sdk()

smtg_add_vst3plugin(CubaseAiAudioTap
    source/cids.h
    source/version.h
    source/shared_memory_ring.h
    source/processor.h
    source/processor.cpp
    source/controller.h
    source/controller.cpp
    source/entry.cpp
)

target_include_directories(CubaseAiAudioTap
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/source
)

target_compile_features(CubaseAiAudioTap
    PUBLIC
        cxx_std_17
)

target_link_libraries(CubaseAiAudioTap
    PRIVATE
        sdk
)

smtg_target_configure_version_file(CubaseAiAudioTap)

if(SMTG_WIN)
    target_sources(CubaseAiAudioTap PRIVATE
        resource/win32resource.rc
    )
    if(MSVC)
        set_property(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR} PROPERTY VS_STARTUP_PROJECT CubaseAiAudioTap)
    endif()
endif()
