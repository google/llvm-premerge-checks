#!/usr/bin/env python3
# Copyright 2020 Google LLC
#
# Licensed under the the Apache License v2.0 with LLVM Exceptions (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://llvm.org/LICENSE.txt
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import asyncio
import logging
import os
from asyncio.subprocess import PIPE
from typing import Callable, AnyStr


async def read_stream_and_display(stream, display):
    while True:
        line = await stream.readline()
        if not line:
            break
        display(line)  # assume it doesn't block


async def read_and_display(write_stdout, write_stderr, *cmd, **kwargs):
    logging.debug(f'subprocess called with {cmd}; {kwargs}')
    process = await asyncio.create_subprocess_shell(*cmd, stdout=PIPE, stderr=PIPE, **kwargs)
    try:
        await asyncio.gather(
            read_stream_and_display(process.stdout, write_stdout),
            read_stream_and_display(process.stderr, write_stderr))
    except Exception:
        process.kill()
        raise
    finally:
        return await process.wait()


def tee(s: AnyStr, write1: Callable[[AnyStr], None], write2: Callable[[AnyStr], None]):
    write1(s)
    write2(s)


def if_not_matches(s: AnyStr, regexp, write: Callable[[AnyStr], None]):
    x = s
    if isinstance(s, (bytes, bytearray)):
        x = s.decode()
    if regexp.match(x) is None:
        write(s)


def watch_shell(write_stdout, write_stderr, *cmd, **kwargs):
    if os.name == 'nt':
        loop = asyncio.ProactorEventLoop()  # Windows
        asyncio.set_event_loop(loop)
    else:
        loop = asyncio.get_event_loop()
    rc = loop.run_until_complete(read_and_display(write_stdout, write_stderr, *cmd, **kwargs))
    return rc
