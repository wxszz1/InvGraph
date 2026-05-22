"""SPN + PL-Marker 融合主逻辑

融合策略：
1. SPN和PL-Marker分别对文本做关系抽取
2. 构建融合特征：[SPN_score, PLM_score, entity_overlap, max_score]
3. 用评分器判定最终三元组
4. 去重：同一(h,r,t)取最高分
"""
import os
import sys
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from relation.fusion.scorer import SklearnFusionScorer, build_fusion_features


class RelationFusion:
    """关系抽取融合器"""

    def __init__(self, scorer_path: str = None, threshold: float = 0.5):
        self.scorer = SklearnFusionScorer()
        self.threshold = threshold

        if scorer_path and os.path.exists(scorer_path):
            self.scorer.load(scorer_path)

    def fuse(self, spn_triples: list, plm_triples: list,
             entities: list = None) -> list:
        """
        融合SPN和PL-Marker的输出

        Args:
            spn_triples: SPN输出的三元组
            plm_triples: PL-Marker输出的三元组
            entities: 实体列表（可选，用于规则补充）
        Returns:
            fused_triples: 融合后的三元组列表
        """
        merged, features = build_fusion_features(spn_triples, plm_triples)

        if len(merged) == 0:
            return []

        if self.scorer.trained:
            scores = self.scorer.predict_proba(features)
        else:
            # 未训练评分器时，取两个模型分数的最大值
            scores = features.max(axis=1)

        # 过滤低置信度
        result = []
        for triple, score in zip(merged, scores):
            if score >= self.threshold:
                result.append({
                    "head": triple["head"],
                    "relation": triple["relation"],
                    "tail": triple["tail"],
                    "confidence": round(float(score), 3),
                    "spn_score": round(triple["spn_score"], 3),
                    "plm_score": round(triple["plm_score"], 3),
                })

        # 按分数排序
        result.sort(key=lambda x: x["confidence"], reverse=True)
        return result

    def train_scorer(self, spn_results, plm_results, gold_triples, save_path=None):
        """
        用标注数据训练融合评分器

        Args:
            spn_results: list of SPN预测结果
            plm_results: list of PL-Marker预测结果
            gold_triples: list of 真实三元组
        """
        all_features = []
        all_labels = []

        for spn, plm, gold in zip(spn_results, plm_results, gold_triples):
            merged, features = build_fusion_features(spn, plm)
            if len(merged) == 0:
                continue

            gold_set = set()
            for g in gold:
                key = (g.get("head", g.get("subject", "")),
                       g["relation"],
                       g.get("tail", g.get("object", "")))
                gold_set.add(key)

            for triple, feat in zip(merged, features):
                key = (triple["head"], triple["relation"], triple["tail"])
                label = 1 if key in gold_set else 0
                all_features.append(feat)
                all_labels.append(label)

        if all_features:
            self.scorer.train(np.array(all_features), np.array(all_labels))
            if save_path:
                self.scorer.save(save_path)
            print(f"融合评分器训练完成: {sum(all_labels)}/{len(all_labels)} 正样本")
