"""FTRL (Follow The Regularized Leader) 在线学习模型

用于实体对齐的在线学习匹配器：
- 特征向量：[edit_sim, jaccard_sim, ngram_sim, type_match]
- 每次有新标注数据时增量更新权重
- 输出：匹配概率 > 阈值 → 合并
"""
import numpy as np
import os
import json


class FTRLMatcher:
    """FTRL在线学习匹配器"""

    def __init__(self, num_features: int = 4, alpha: float = 0.1,
                 beta: float = 1.0, l1: float = 0.1, l2: float = 1.0):
        self.num_features = num_features
        self.alpha = alpha
        self.beta = beta
        self.l1 = l1
        self.l2 = l2

        # FTRL状态
        self.w = np.zeros(num_features)       # 权重
        self.z = np.zeros(num_features)       # 累积梯度
        self.n = np.zeros(num_features)       # 累积梯度平方

        # 初始化权重（偏向编辑距离相似度）
        self.w = np.array([0.5, 0.3, 0.3, 0.2])
        self.z = self.w.copy()

    def _sigmoid(self, x):
        return 1.0 / (1.0 + np.exp(-np.clip(x, -20, 20)))

    def predict_proba(self, features: np.ndarray) -> np.ndarray:
        """
        预测匹配概率

        Args:
            features: (N, 4) 特征矩阵
        Returns:
            probs: (N,) 匹配概率
        """
        scores = features @ self.w
        return self._sigmoid(scores)

    def predict(self, features: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        """预测是否匹配"""
        return (self.predict_proba(features) >= threshold).astype(int)

    def update(self, features: np.ndarray, labels: np.ndarray):
        """
        FTRL在线更新

        Args:
            features: (N, 4)
            labels: (N,) 0或1
        """
        for i in range(len(features)):
            x = features[i]
            y = labels[i]
            p = self._sigmoid(x @ self.w)
            g = (p - y) * x  # 梯度

            for j in range(self.num_features):
                if abs(self.z[j]) <= self.l1:
                    self.w[j] = 0.0
                else:
                    sign = np.sign(self.z[j])
                    self.w[j] = -(self.z[j] - sign * self.l1) / (
                        (self.beta + np.sqrt(self.n[j])) / self.alpha + self.l2
                    )

                self.n[j] += g[j] ** 2
                sigma = (np.sqrt(self.n[j]) - np.sqrt(self.n[j] - g[j] ** 2)) / self.alpha
                self.z[j] += g[j] - sigma * self.w[j]

    def train_batch(self, features: np.ndarray, labels: np.ndarray, epochs: int = 10):
        """批量训练"""
        for _ in range(epochs):
            indices = np.random.permutation(len(features))
            self.update(features[indices], labels[indices])

    def save(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = {
            "w": self.w.tolist(), "z": self.z.tolist(), "n": self.n.tolist(),
            "num_features": self.num_features,
        }
        with open(path, 'w') as f:
            json.dump(data, f)

    def load(self, path: str):
        with open(path, 'r') as f:
            data = json.load(f)
        self.w = np.array(data["w"])
        self.z = np.array(data["z"])
        self.n = np.array(data["n"])
