"""SPN + PL-Marker Stacking融合框架"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from relation.spn.inference import SPNInference
from relation.pl_marker.inference import PLMarkerInference


class StackingFusion:
    """单层Stacking融合SPN与PL-Marker的抽取结果"""

    def __init__(self, spn_ckpt=None, plm_ckpt=None):
        self.spn = None
        self.plm = None
        self.spn_weight = 0.4
        self.plm_weight = 0.6

        # 尝试加载模型（如果checkpoint存在）
        if spn_ckpt and os.path.exists(spn_ckpt):
            try:
                self.spn = SPNInference(spn_ckpt)
                print("[StackingFusion] SPN model loaded")
            except Exception as e:
                print(f"[StackingFusion] SPN load failed: {e}")

        if plm_ckpt and os.path.exists(plm_ckpt):
            try:
                self.plm = PLMarkerInference(plm_ckpt)
                print("[StackingFusion] PL-Marker model loaded")
            except Exception as e:
                print(f"[StackingFusion] PL-Marker load failed: {e}")

    @property
    def available(self):
        return self.spn is not None or self.plm is not None

    def predict(self, text, threshold=0.5):
        """融合预测：返回融合后的三元组列表"""
        spn_triples = []
        plm_triples = []

        if self.spn:
            try:
                spn_triples = self.spn.predict(text, threshold=threshold)
            except Exception:
                pass

        if self.plm:
            try:
                plm_triples = self.plm.predict(text, entities=None)
            except Exception:
                pass

        return self._fuse(spn_triples, plm_triples)

    def _fuse(self, spn_triples, plm_triples):
        """加权投票融合"""
        if not spn_triples and not plm_triples:
            return []
        if not spn_triples:
            return plm_triples
        if not plm_triples:
            return spn_triples

        # 构建 (head, relation, object) -> score 映射
        triple_scores = {}
        for t in spn_triples:
            key = (t.get("subject", t.get("head", "")),
                   t["relation"],
                   t.get("object", t.get("tail", "")))
            triple_scores[key] = triple_scores.get(key, 0) + self.spn_weight

        for t in plm_triples:
            key = (t.get("head", t.get("subject", "")),
                   t["relation"],
                   t.get("tail", t.get("object", "")))
            triple_scores[key] = triple_scores.get(key, 0) + self.plm_weight

        # 取得分 >= 0.5 的三元组
        result = []
        for (head, rel, tail), score in triple_scores.items():
            if score >= 0.5:
                result.append({"head": head, "relation": rel, "tail": tail})

        return result
