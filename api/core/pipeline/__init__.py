"""
Pipeline execution module for Celery tasks.
Provides reusable functions for executing pipeline stages.
"""

from api.core.pipeline.executor import execute_pipeline_stages
from api.core.pipeline.status import mark_pipeline_as_failed

__all__ = [
    'execute_pipeline_stages',
    'mark_pipeline_as_failed',
]

