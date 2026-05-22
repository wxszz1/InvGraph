"""SPN 损失函数

包含：
- 匹配损失（L_match）：匈牙利匹配后的交叉熵
- 实体位置损失（L_entity）：subject/object位置预测的交叉熵
- 关系损失（L_relation）：关系分类的交叉熵
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


class SetPredictionLoss(nn.Module):
    """集合预测损失"""

    def __init__(self, num_relations: int, num_queries: int = 30,
                 no_relation_weight: float = 0.1):
        super().__init__()
        self.num_relations = num_relations
        self.num_queries = num_queries
        self.no_relation_weight = no_relation_weight

        # 类别权重（降低None类权重）
        weight = torch.ones(num_relations)
        weight[-1] = no_relation_weight
        self.register_buffer("rel_weight", weight)

    def forward(self, pred_scores, pred_subj_dist, pred_obj_dist, gt_triples,
                matcher_matches):
        """
        Args:
            pred_scores: (Q, R) 关系logits
            pred_subj_dist: (Q, S) subject位置分布
            pred_obj_dist: (Q, S) object位置分布
            gt_triples: list of (subj_start, subj_end, rel, obj_start, obj_end)
            matcher_matches: list of (query_idx, gt_idx) 匈牙利匹配结果
        Returns:
            total_loss, loss_dict
        """
        device = pred_scores.device
        num_queries = pred_scores.size(0)

        if len(gt_triples) == 0 or len(matcher_matches) == 0:
            # 没有真实三元组：所有query预测None
            no_rel_target = torch.full((num_queries,), self.num_relations - 1,
                                       dtype=torch.long, device=device)
            loss = F.cross_entropy(pred_scores, no_rel_target,
                                   weight=self.rel_weight)
            return loss, {"relation": loss.item(), "entity": 0.0}

        # 构建目标
        matched_queries = [m[0] for m in matcher_matches]
        matched_gts = [m[1] for m in matcher_matches]

        # 关系损失
        rel_targets = torch.full((num_queries,), self.num_relations - 1,
                                 dtype=torch.long, device=device)
        subj_targets = torch.zeros(num_queries, pred_subj_dist.size(-1),
                                   device=device)
        obj_targets = torch.zeros(num_queries, pred_obj_dist.size(-1),
                                  device=device)

        for q_idx, gt_idx in zip(matched_queries, matched_gts):
            gt = gt_triples[gt_idx]
            subj_start, subj_end, rel, obj_start, obj_end = gt

            rel_targets[q_idx] = rel
            subj_targets[q_idx, subj_start] = 0.5
            subj_targets[q_idx, subj_end] = 0.5
            obj_targets[q_idx, obj_start] = 0.5
            obj_targets[q_idx, obj_end] = 0.5

        # 归一化位置目标
        subj_sum = subj_targets.sum(dim=-1, keepdim=True).clamp(min=1)
        obj_sum = obj_targets.sum(dim=-1, keepdim=True).clamp(min=1)
        subj_targets = subj_targets / subj_sum
        obj_targets = obj_targets / obj_sum

        # 损失计算
        loss_rel = F.cross_entropy(pred_scores, rel_targets, weight=self.rel_weight)
        loss_subj = -(subj_targets * F.log_softmax(pred_subj_dist, dim=-1)).sum(-1).mean()
        loss_obj = -(obj_targets * F.log_softmax(pred_obj_dist, dim=-1)).sum(-1).mean()

        total_loss = loss_rel + loss_subj + loss_obj

        return total_loss, {
            "relation": loss_rel.item(),
            "entity": (loss_subj.item() + loss_obj.item()) / 2,
        }
