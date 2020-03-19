#!/bin/bash
set -eux

cd /tests/llvm-project
mkdir -p build
cd build
cmake -G Ninja ../llvm -DLLVM_BUILD_EXAMPLES=ON -DLLVM_ENABLE_CXX1Y=Y -DLLVM_TARGETS_TO_BUILD="host;NVPTX" -DLLVM_ENABLE_PROJECTS=mlir -DMLIR_CUDA_RUNNER_ENABLED=1 -DCMAKE_CUDA_COMPILER=/usr/local/cuda/bin/nvcc

cmake --build . --target check-mlir
