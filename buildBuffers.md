## Compiling Protocol Buffers

1. Clone Flow repo for protocol buffer source files `git clone git@github.com:onflow/flow.git`.

2. Compile protocol buffers for Python with `protoc` which is included in `grpcio-tools`:
    1. Download latest platform release (e.g. `protoc-3.15.6-linux-x86_64.zip`) from https://github.com/protocolbuffers/protobuf/releases. This contains `protoc` binary and Google includes neccessary for compiling.
    2. Extract `include` directory from the release and place this in the same directory containing `flow/protobuf/flow`.
    3. Create a build directory (e.g. `mkdir build`) and compile the protocol buffer source (`.proto` files) inside `flow/protobuf/flow` with 
    
        ```python -m grpc_tools.protoc -I. --python_out=build/ --grpc_python_out=build/ flow/access/access.proto flow/entities/account.proto flow/entities/block_header.proto flow/entities/block_seal.proto flow/entities/block.proto flow/entities/collection.proto flow/entities/event.proto flow/entities/transaction.proto flow/execution/execution.proto google/protobuf/timestamp.proto```

        This must be run from the directory containing the build directory and the `flow` directory which contains `access`, `entities` etc. This command uses the `protoc` binary included in `grpcio-tools`. Output is saved to `build`.
        Reference (https://grpc.io/docs/languages/python/quickstart/).