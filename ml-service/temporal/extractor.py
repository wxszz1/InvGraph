"""时序四元组生成模块

将时间表达式关联到三元组，生成时序四元组：
{ head, relation, tail, time }

时间关联策略：
1. 按句子位置关联：时间离三元组越近，关联度越高
2. 每个三元组关联最近的时间表达式
3. 无时间的三元组标记为 None
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from temporal.normalizer import TimeNormalizer


class TemporalQuadrupleExtractor:
    """时序四元组提取器"""

    def __init__(self):
        self.normalizer = TimeNormalizer()

    def extract(self, text: str, triples: list) -> list:
        """
        为三元组附加时间信息

        Args:
            text: 原始文本
            triples: 三元组列表 [{"head": ..., "relation": ..., "tail": ...}, ...]
        Returns:
            quadruples: [{head, relation, tail, time}, ...]
        """
        # 提取时间表达式
        time_exprs = self.normalizer.extract_and_normalize(text)

        if not triples:
            return []

        if not time_exprs:
            # 无时间信息
            return [{
                **t, "time": None
            } for t in triples]

        # 将文本按时间分割，判断每个三元组属于哪个时间片段
        quadruples = []
        for triple in triples:
            # 查找三元组在文本中的位置
            head_pos = text.find(triple["head"])
            tail_pos = text.find(triple["tail"])

            if head_pos < 0 and tail_pos < 0:
                # 找不到位置，关联第一个时间
                time_val = time_exprs[0]["normalized"]
            else:
                ref_pos = max(head_pos, tail_pos) if head_pos >= 0 and tail_pos >= 0 else max(head_pos, tail_pos)
                # 找最近的时间
                best_time = time_exprs[0]["normalized"]
                best_dist = float('inf')
                for te in time_exprs:
                    dist = abs(te["start"] - ref_pos)
                    if dist < best_dist:
                        best_dist = dist
                        best_time = te["normalized"]
                time_val = best_time

            quadruples.append({
                "head": triple["head"],
                "relation": triple["relation"],
                "tail": triple["tail"],
                "time": time_val,
            })

        return quadruples

    def extract_from_text(self, text: str, spn_triples: list = None,
                          plm_triples: list = None) -> dict:
        """
        完整的时序四元组提取流程

        Returns:
            {
                "times": [...],
                "quadruples": [...]
            }
        """
        times = self.normalizer.extract_and_normalize(text)

        # 合并两个模型的三元组
        all_triples = []
        seen = set()
        for t in (spn_triples or []) + (plm_triples or []):
            key = (t.get("head", t.get("subject", "")),
                   t["relation"],
                   t.get("tail", t.get("object", "")))
            if key not in seen:
                seen.add(key)
                all_triples.append({
                    "head": key[0], "relation": key[1], "tail": key[2]
                })

        quadruples = self.extract(text, all_triples)

        return {
            "times": times,
            "quadruples": quadruples,
        }
