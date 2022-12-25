#!/usr/bin/env bash
[ ! -d llvm-project ] && git clone https://github.com/llvm/llvm-project.git llvm-project
cd llvm-project
git fetch --all
git checkout ${1:-20ba079dda7be1a72d64cebc9f55d909bf29f6c1}
rm -rf build
mkdir build
cd build
export CC="clang"
export CXX="clang++"
export LD="LLD"
cmake ../llvm -D LLVM_ENABLE_PROJECTS="bolt;compiler-rt;libc;pstl;polly;llvm;libclc;clang;mlir;clang-tools-extra;flang;lld" -G Ninja -D CMAKE_BUILD_TYPE=Release -D LLVM_ENABLE_ASSERTIONS=ON -D LLVM_BUILD_EXAMPLES=ON -D LLVM_LIT_ARGS="-v --xunit-xml-output test-results.xml --resultdb-output resultdb.json" -D LLVM_ENABLE_LLD=ON -D CMAKE_CXX_FLAGS=-gmlt -DBOLT_CLANG_EXE=/usr/bin/clang
# ^note that compiler cache arguments are omitted
ln -s $PWD/compile_commands.json ../compile_commands.json
ninja check-all
