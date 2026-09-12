"""Stops that are not failures.

A lock waiting on a human and a stage waiting on an agent are both the pipeline
working correctly. Recording them as failures makes `studio status` unreadable at
exactly the moment an operator needs it: after a long run, the one thing they must
know is whether the thing that stopped needs a decision or needs debugging.
"""

from __future__ import annotations


class PipelineHalt(RuntimeError):
    """The run stopped on purpose and is waiting for someone. Never a defect."""
