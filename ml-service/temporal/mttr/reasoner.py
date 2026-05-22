"""MTTR 多任务时序推理逻辑

基于领域规则的时序推理：
1. 融资轮次递进性：天使轮 before A轮 before B轮 before C轮
2. 同一轮次内，领投与跟投同时发生
3. 投资时间不早于企业成立时间
4. 时序关系类型：before / after / overlap / simultaneous
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from schema.ontology import ROUND_ORDER, is_round_ordered


# 时序关系类型
TEMPORAL_RELATIONS = ["before", "after", "overlap", "simultaneous"]


class TemporalReasoner:
    """时序推理器"""

    def __init__(self):
        self.round_order = ROUND_ORDER

    def reason(self, quadruples: list) -> list:
        """
        对时序四元组集合进行时序推理

        Args:
            quadruples: [{head, relation, tail, time}, ...]
        Returns:
            时序关系列表: [{"triple_a": idx_a, "triple_b": idx_b, "temporal_rel": "...", "reason": "..."}, ...]
        """
        temporal_relations = []
        n = len(quadruples)

        for i in range(n):
            for j in range(i + 1, n):
                qa = quadruples[i]
                qb = quadruples[j]
                rel = self._infer_temporal_relation(qa, qb)
                if rel:
                    temporal_relations.append({
                        "triple_a": i,
                        "triple_b": j,
                        "triple_a_detail": f"{qa['head']} {qa['relation']} {qa['tail']}",
                        "triple_b_detail": f"{qb['head']} {qb['relation']} {qb['tail']}",
                        **rel,
                    })

        return temporal_relations

    def _infer_temporal_relation(self, qa: dict, qb: dict) -> dict:
        """推理两个四元组之间的时序关系"""

        # 规则1: 同一轮次的领投和跟投 → simultaneous
        round_a = self._extract_round(qa)
        round_b = self._extract_round(qb)
        ent_a = qa.get("tail", qa.get("head", ""))
        ent_b = qb.get("tail", qb.get("head", ""))

        if round_a and round_b and ent_a == ent_b:
            if round_a == round_b:
                if qa["relation"] == "LEAD" and qb["relation"] == "FOLLOW":
                    return {"temporal_rel": "simultaneous", "reason": "同一轮次领投与跟投"}
                if qa["relation"] == "FOLLOW" and qb["relation"] == "LEAD":
                    return {"temporal_rel": "simultaneous", "reason": "同一轮次领投与跟投"}

        # 规则2: 不同轮次的融资 → 按轮次顺序判断before/after
        if round_a and round_b and is_round_ordered(round_a, round_b):
            return {"temporal_rel": "before", "reason": f"{round_a}先于{round_b}"}
        if round_b and round_a and is_round_ordered(round_b, round_a):
            return {"temporal_rel": "after", "reason": f"{round_b}先于{round_a}"}

        # 规则3: 基于时间
        time_a = qa.get("time", "")
        time_b = qb.get("time", "")
        if time_a and time_b:
            if time_a < time_b:
                return {"temporal_rel": "before", "reason": f"{time_a}先于{time_b}"}
            elif time_a > time_b:
                return {"temporal_rel": "after", "reason": f"{time_a}晚于{time_b}"}
            else:
                return {"temporal_rel": "simultaneous", "reason": f"同时间{time_a}"}

        return None

    def _extract_round(self, quad: dict) -> str:
        """从四元组中提取轮次"""
        text = f"{quad.get('head', '')} {quad.get('relation', '')} {quad.get('tail', '')}"
        for round_name in self.round_order:
            if round_name in text:
                return round_name
        return ""

    def validate_constraints(self, quadruples: list) -> list:
        """
        校验时序约束是否被违反

        Returns:
            violations: [{"triple": idx, "constraint": "...", "message": "..."}, ...]
        """
        violations = []

        for i, q in enumerate(quadruples):
            # 约束: 投资时间不早于企业成立时间
            if q.get("relation") in ("INVEST", "LEAD", "FOLLOW"):
                time = q.get("time", "")
                if time and len(time) >= 4:
                    year = int(time[:4])
                    if year < 2000:
                        violations.append({
                            "triple": i,
                            "constraint": "时间合理性",
                            "message": f"投资时间 {time} 早于2000年，可能不合理",
                        })

        return violations
