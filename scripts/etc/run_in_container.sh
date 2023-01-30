# Sample script that you can run in docker container to build vllm
#!/usr/bin/env bash
su buildkite-agent
cd /var/lib/buildkite-agent
git clone https://github.com/llvm-premerge-tests/llvm-project.git llvm-project
cd llvm-project
rm -rf build
mkdir build
cd build
export CC="clang"
export CXX="clang++"
export LD="LLD"
cmake ../llvm -D LLVM_ENABLE_PROJECTS="clang;mlir;lldb;llvm" -G Ninja -D CMAKE_BUILD_TYPE=Release -D LLVM_ENABLE_ASSERTIONS=ON -D LLVM_BUILD_EXAMPLES=ON -D LLVM_LIT_ARGS="-v --xunit-xml-output test-results.xml" -D LLVM_ENABLE_LLD=ON -D CMAKE_CXX_FLAGS=-gmlt -DBOLT_CLANG_EXE=/usr/bin/clang
