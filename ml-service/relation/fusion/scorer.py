"""融合评分器

将SPN和PL-Marker的输出进行特征拼接，
通过一个小型MLP判定最终保留/丢弃。
"""
import torch
import torch.nn as nn
import numpy as np
from sklearn.linear_model import LogisticRegression
import pickle
import os


class FusionScorer(nn.Module):
    """融合评分器（MLP版本）"""

    def __init__(self, input_dim: int = 4, hidden_dim: int = 32):
        super().__init__()
        self.scorer = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid(),
        )

    def forward(self, features):
        """features: (batch, 4) → score: (batch, 1)"""
        return self.scorer(features)


class SklearnFusionScorer:
    """融合评分器（sklearn LogisticRegression版本，更快训练）"""

    def __init__(self):
        self.model = LogisticRegression(
            C=1.0, max_iter=1000, class_weight="balanced"
        )
        self.trained = False

    def train(self, features, labels):
        """训练融合器"""
        self.model.fit(features, labels)
        self.trained = True

    def predict_proba(self, features):
        """预测保留概率"""
        if not self.trained:
            return np.ones(len(features)) * 0.5
        return self.model.predict_proba(features)[:, 1]

    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump(self.model, f)

    def load(self, path):
        with open(path, 'rb') as f:
            self.model = pickle.load(f)
        self.trained = True


def build_fusion_features(spn_triples, plm_triples):
    """
    为SPN和PL-Marker的候选三元组构建融合特征

    Args:
        spn_triples: [{"subject": ..., "relation": ..., "object": ..., "confidence": ...}, ...]
        plm_triples: [{"head": ..., "relation": ..., "tail": ..., "confidence": ...}, ...]
    Returns:
        merged: 合并后的三元组列表，每个含fusion_features
        features: (N, 4) 特征矩阵
    """
    # 标准化格式
    spn_norm = []
    for t in spn_triples:
        spn_norm.append({
            "head": t.get("subject", t.get("head", "")),
            "relation": t.get("relation", ""),
            "tail": t.get("object", t.get("tail", "")),
            "spn_score": t.get("confidence", 0.5),
            "plm_score": 0.0,
        })

    plm_norm = []
    for t in plm_triples:
        plm_norm.append({
            "head": t.get("head", t.get("subject", "")),
            "relation": t.get("relation", ""),
            "tail": t.get("tail", t.get("object", "")),
            "spn_score": 0.0,
            "plm_score": t.get("confidence", 0.5),
        })

    # 合并：同一 (head, relation, tail) 合并分数
    merged_map = {}
    for t in spn_norm:
        key = (t["head"], t["relation"], t["tail"])
        if key in merged_map:
            merged_map[key]["spn_score"] = max(merged_map[key]["spn_score"], t["spn_score"])
        else:
            merged_map[key] = dict(t)

    for t in plm_norm:
        key = (t["head"], t["relation"], t["tail"])
        if key in merged_map:
            merged_map[key]["plm_score"] = max(merged_map[key]["plm_score"], t["plm_score"])
        else:
            merged_map[key] = dict(t)

    merged = list(merged_map.values())

    # 构建特征矩阵
    features = []
    for t in merged:
        entity_overlap = 1.0 if t["spn_score"] > 0 and t["plm_score"] > 0 else 0.0
        max_score = max(t["spn_score"], t["plm_score"])
        features.append([
            t["spn_score"], t["plm_score"],
            entity_overlap, max_score,
        ])

    return merged, np.array(features) if features else np.empty((0, 4))
