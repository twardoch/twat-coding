#!/usr/bin/env -S uv run
"""Memory monitoring utilities."""

import ast
import asyncio
import gc
import os
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Generator

import psutil
from loguru import logger
from memory_profiler import profile as memory_profile


@dataclass
class MemoryStats:
    """Memory usage statistics."""

    rss: int  # Resident Set Size in bytes
    vms: int  # Virtual Memory Size in bytes
    shared: int  # Shared memory in bytes
    text: int  # Text segment memory in bytes
    data: int  # Data segment memory in bytes
    lib: int  # Library memory in bytes
    dirty: int  # Dirty pages in bytes
    peak_rss: int  # Peak RSS memory in bytes


class MemoryMonitor:
    """Monitor memory usage of the process."""

    def __init__(self, interval: float = 1.0) -> None:
        """Initialize the memory monitor.

        Args:
            interval: Monitoring interval in seconds
        """
        self.interval = interval
        self._process = psutil.Process(os.getpid())
        self._stop_event = threading.Event()
        self._stats: list[MemoryStats] = []
        self._monitor_thread: threading.Thread | None = None

    def start(self) -> None:
        """Start monitoring memory usage."""
        if self._monitor_thread is not None:
            return

        def _monitor() -> None:
            while not self._stop_event.is_set():
                try:
                    meminfo = self._process.memory_info()
                    stats = MemoryStats(
                        rss=meminfo.rss,
                        vms=meminfo.vms,
                        shared=meminfo.shared,
                        text=meminfo.text,
                        data=meminfo.data,
                        lib=meminfo.lib,
                        dirty=meminfo.dirty,
                        peak_rss=self._process.memory_info().rss,
                    )
                    self._stats.append(stats)
                    logger.debug(
                        f"Memory usage: RSS={stats.rss / 1024 / 1024:.1f}MB, "
                        f"VMS={stats.vms / 1024 / 1024:.1f}MB"
                    )
                except Exception as e:
                    logger.error(f"Failed to collect memory stats: {e}")
                self._stop_event.wait(self.interval)

        self._monitor_thread = threading.Thread(target=_monitor, daemon=True)
        self._monitor_thread.start()

    def stop(self) -> None:
        """Stop monitoring memory usage."""
        if self._monitor_thread is None:
            return
        self._stop_event.set()
        self._monitor_thread.join()
        self._monitor_thread = None

    @property
    def stats(self) -> list[MemoryStats]:
        """Get collected memory statistics."""
        return self._stats.copy()

    @property
    def peak_memory(self) -> int:
        """Get peak memory usage in bytes."""
        if not self._stats:
            return 0
        return max(stat.peak_rss for stat in self._stats)

    def clear_stats(self) -> None:
        """Clear collected statistics."""
        self._stats.clear()


@contextmanager
def memory_monitor(interval: float = 1.0) -> Generator[MemoryMonitor, None, None]:
    """Context manager for memory monitoring.

    Args:
        interval: Monitoring interval in seconds

    Yields:
        Memory monitor instance
    """
    monitor = MemoryMonitor(interval)
    monitor.start()
    try:
        yield monitor
    finally:
        monitor.stop()


async def stream_process_ast(
    node: Any,
    chunk_size: int = 1000,
    gc_interval: int = 10,
) -> AsyncGenerator[list[Any], None]:
    """Process AST nodes in chunks to reduce memory usage.

    Args:
        node: AST node to process
        chunk_size: Number of nodes to process in each chunk
        gc_interval: Number of chunks between garbage collection

    Yields:
        Lists of processed AST nodes
    """
    nodes = list(ast.walk(node))
    chunks = [nodes[i : i + chunk_size] for i in range(0, len(nodes), chunk_size)]

    for i, chunk in enumerate(chunks):
        # Process nodes in the chunk
        processed = []
        for node in chunk:
            # Add your node processing logic here
            processed.append(node)

        # Run garbage collection periodically
        if i > 0 and i % gc_interval == 0:
            gc.collect()

        # Let other tasks run
        await asyncio.sleep(0)

        yield processed


def profile_memory(func: Any) -> Any:
    """Decorator to profile memory usage of a function.

    Args:
        func: Function to profile

    Returns:
        Profiled function
    """
    return memory_profile(func)
