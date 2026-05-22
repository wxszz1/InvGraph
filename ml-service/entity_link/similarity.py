"""实体相似度计算

特征向量：
- 最小编辑距离（名称相似度，归一化到0-1）
- Jaccard系数（属性集合相似度）
- 字符级n-gram相似度
- 类型一致性（0或1）
"""
from typing import Dict


def edit_distance(s1: str, s2: str) -> int:
    """最小编辑距离"""
    m, n = len(s1), len(s2)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, n + 1):
            temp = dp[j]
            if s1[i-1] == s2[j-1]:
                dp[j] = prev
            else:
                dp[j] = 1 + min(prev, dp[j], dp[j-1])
            prev = temp
    return dp[n]


def normalized_edit_similarity(s1: str, s2: str) -> float:
    """归一化编辑距离相似度 (0-1)"""
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    max_len = max(len(s1), len(s2))
    dist = edit_distance(s1, s2)
    return 1.0 - dist / max_len


def jaccard_similarity(s1: str, s2: str) -> float:
    """字符级Jaccard系数"""
    if not s1 and not s2:
        return 1.0
    set1 = set(s1)
    set2 = set(s2)
    if not set1 and not set2:
        return 1.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0


def ngram_similarity(s1: str, s2: str, n: int = 2) -> float:
    """字符级n-gram相似度"""
    if len(s1) < n or len(s2) < n:
        return jaccard_similarity(s1, s2)

    def get_ngrams(s, n):
        return set(s[i:i+n] for i in range(len(s) - n + 1))

    ng1 = get_ngrams(s1, n)
    ng2 = get_ngrams(s2, n)
    if not ng1 and not ng2:
        return 1.0
    intersection = len(ng1 & ng2)
    union = len(ng1 | ng2)
    return intersection / union if union > 0 else 0.0


def type_match(e1: Dict, e2: Dict) -> float:
    """类型一致性"""
    return 1.0 if e1.get("type") == e2.get("type") else 0.0


def compute_similarity_features(e1: Dict, e2: Dict) -> list:
    """
    计算两个实体的相似度特征向量

    Returns:
        [edit_sim, jaccard_sim, ngram_sim, type_match]
    """
    name1 = e1.get("name", "")
    name2 = e2.get("name", "")

    return [
        normalized_edit_similarity(name1, name2),
        jaccard_similarity(name1, name2),
        ngram_similarity(name1, name2),
        type_match(e1, e2),
    ]
