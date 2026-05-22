"""FTRLIM实体对齐模块

Blocker分块 → Similarity特征提取 → FTRLMatcher匹配 → Validator时序约束
"""
from .aligner import EntityAligner
from .blocker import Blocker
from .similarity import compute_similarity_features
from .matcher import FTRLMatcher
from .validator import TemporalValidator
