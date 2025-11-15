"""
Continual Learning: Model học thêm mà không quên kiến thức cũ.
"""

from .rehearsal_buffer import RehearsalBuffer
from .ewc import ElasticWeightConsolidation
from .incremental_finetuning import IncrementalFineTuning

__all__ = ['RehearsalBuffer', 'ElasticWeightConsolidation', 'IncrementalFineTuning']

