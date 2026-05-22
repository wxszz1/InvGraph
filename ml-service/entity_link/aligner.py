"""实体对齐主流程

Pipeline: Blocker分块 → Similarity特征 → FTRLMatcher匹配 → 合并
- 输入：实体列表
- 输出：合并组（同一实体的不同表述归为一组）
- 支持增量更新：新实体到来时只与已有实体比较
"""
import numpy as np
from typing import List, Dict, Tuple, Optional
from .blocker import Blocker
from .similarity import compute_similarity_features
from .matcher import FTRLMatcher


class EntityAligner:
    """实体对齐器"""

    def __init__(self, threshold: float = 0.6, model_path: Optional[str] = None):
        self.threshold = threshold
        self.blocker = Blocker(strategy="type+initial")
        self.matcher = FTRLMatcher(num_features=4)
        if model_path:
            self.matcher.load(model_path)

    def align(self, entities: List[Dict]) -> List[List[int]]:
        """
        对实体列表做对齐，返回合并组

        Args:
            entities: [{"name": ..., "type": ..., ...}, ...]
        Returns:
            merge_groups: [[idx1, idx2, ...], ...] 每组内实体应合并
        """
        if len(entities) < 2:
            return [[i] for i in range(len(entities))]

        # 1. 分块，获取候选对
        blocks = self.blocker.block(entities)

        # 2. 计算特征 + 预测匹配概率
        pairs_scores = []
        for block_pairs in blocks:
            if not block_pairs:
                continue
            features = np.array([
                compute_similarity_features(entities[i], entities[j])
                for i, j in block_pairs
            ])
            probs = self.matcher.predict_proba(features)
            for k, (i, j) in enumerate(block_pairs):
                if probs[k] >= self.threshold:
                    pairs_scores.append((i, j, float(probs[k])))

        # 3. 按分数降序，贪心合并（并查集）
        pairs_scores.sort(key=lambda x: x[2], reverse=True)
        parent = list(range(len(entities)))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x, y):
            rx, ry = find(x), find(y)
            if rx != ry:
                parent[rx] = ry

        for i, j, _ in pairs_scores:
            union(i, j)

        # 4. 收集合并组
        groups = {}
        for i in range(len(entities)):
            root = find(i)
            groups.setdefault(root, []).append(i)

        return list(groups.values())

    def update_with_feedback(self, entity_pairs: List[Tuple[Dict, Dict]],
                              labels: List[int]):
        """
        用人工标注反馈增量更新模型

        Args:
            entity_pairs: [(entity_a, entity_b), ...]
            labels: 1=匹配, 0=不匹配
        """
        features = np.array([
            compute_similarity_features(a, b)
            for a, b in entity_pairs
        ])
        labels_arr = np.array(labels, dtype=np.float64)
        self.matcher.update(features, labels_arr)

    def train(self, entity_pairs: List[Tuple[Dict, Dict]],
              labels: List[int], epochs: int = 10):
        """批量训练匹配模型"""
        features = np.array([
            compute_similarity_features(a, b)
            for a, b in entity_pairs
        ])
        labels_arr = np.array(labels, dtype=np.float64)
        self.matcher.train_batch(features, labels_arr, epochs=epochs)

    def save_model(self, path: str):
        self.matcher.save(path)

    def load_model(self, path: str):
        self.matcher.load(path)
