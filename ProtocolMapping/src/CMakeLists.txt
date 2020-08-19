cmake_minimum_required(VERSION 3.5.1)
project(ProtocolMapping C CXX)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")

find_package(Threads REQUIRED)
set(protobuf_MODULE_COMPATIBLE TRUE)
find_package(Protobuf CONFIG REQUIRED)
message(STATUS "Using protobuf ${protobuf_VERSION}")

set(_PROTOBUF_LIBPROTOBUF protobuf::libprotobuf)
set(_REFLECTION gRPC::grpc++_reflection)
find_program(_PROTOBUF_PROTOC protoc)

find_package(gRPC CONFIG REQUIRED)
message(STATUS "Using gRPC ${gRPC_VERSION}")
set(_GRPC_GRPCPP gRPC::grpc++)

find_program(_GRPC_CPP_PLUGIN_EXECUTABLE grpc_cpp_plugin)

get_filename_component(hw_proto "./mapping.proto" ABSOLUTE)
get_filename_component(hw_proto_path "${hw_proto}" PATH)

set(hw_proto_srcs "./mapping.pb.cc")
set(hw_proto_hdrs "./mapping.pb.h")
set(hw_grpc_srcs "./mapping.grpc.pb.cc")
set(hw_grpc_hdrs "./mapping.grpc.pb.h")

add_custom_command(
    OUTPUT "${hw_proto_srcs}" "${hw_proto_hdrs}" "${hw_grpc_srcs}" "${hw_grpc_hdrs}"
    COMMAND ${_PROTOBUF_PROTOC}
    ARGS --grpc_out "."
    --cpp_out "."
    -I "${hw_proto_path}"
    --plugin=protoc-gen-grpc="${_GRPC_CPP_PLUGIN_EXECUTABLE}"
    "${hw_proto}"
    DEPENDS "${hw_proto}")

INCLUDE_DIRECTORIES("/grpc" "./build"  "/root/.local/bin" "/usr/include" "/usr/local/include")

add_executable(mapping_server "mapping_server.cc" ${hw_proto_srcs} ${hw_grpc_srcs})
target_link_libraries(mapping_server ${_REFLECTION} ${_GRPC_GRPCPP} ${_PROTOBUF_LIBPROTOBUF} libwiringPi.so libmodbus.so z /root/.local/lib/libgrpc.a)