"""SPN Hungarian二分匹配

将预测的三元组集合与真实三元组集合做最优匹配。
使用scipy的linear_sum_assignment实现匈牙利算法。
"""
import torch
from scipy.optimize import linear_sum_assignment


class HungarianMatcher:
    """匈牙利匹配器：找到预测集合和真实集合的最优匹配"""

    def __init__(self, cost_class: float = 1.0, cost_entity: float = 1.0):
        self.cost_class = cost_class
        self.cost_entity = cost_entity

    @torch.no_grad()
    def __call__(self, pred_scores, pred_subj, pred_obj, gt_triples):
        """
        Args:
            pred_scores: (num_queries, num_relations) 每个query的关系概率
            pred_subj: (num_queries, seq_len) 每个query预测的subject位置分布
            pred_obj: (num_queries, seq_len) 每个query预测的object位置分布
            gt_triples: list of (subj_start, subj_end, relation, obj_start, obj_end)
        Returns:
            List of (query_idx, gt_idx) pairs
        """
        num_queries = pred_scores.size(0)
        num_gt = len(gt_triples)

        if num_gt == 0:
            return []

        # 计算匹配代价矩阵
        # 关系分类代价：1 - P(correct_relation)
        pred_probs = pred_scores.softmax(-1)  # (Q, R)
        cost_class_matrix = torch.zeros(num_queries, num_gt, device=pred_scores.device)

        for j, gt in enumerate(gt_triples):
            gt_rel = gt[2]
            cost_class_matrix[:, j] = 1 - pred_probs[:, gt_rel]

        # 实体位置代价
        pred_subj_probs = pred_subj.softmax(-1)  # (Q, S)
        pred_obj_probs = pred_obj.softmax(-1)     # (Q, S)
        cost_entity_matrix = torch.zeros(num_queries, num_gt, device=pred_scores.device)

        for j, gt in enumerate(gt_triples):
            subj_start, subj_end = gt[0], gt[1]
            obj_start, obj_end = gt[3], gt[4]

            # 用预测分布中gt位置的概率来衡量代价
            subj_prob = (pred_subj_probs[:, subj_start] + pred_subj_probs[:, subj_end]) / 2
            obj_prob = (pred_obj_probs[:, obj_start] + pred_obj_probs[:, obj_end]) / 2
            cost_entity_matrix[:, j] = 2 - subj_prob - obj_prob

        # 总代价
        C = self.cost_class * cost_class_matrix + self.cost_entity * cost_entity_matrix
        C = C.cpu().numpy()

        # 匈牙利算法
        row_ind, col_ind = linear_sum_assignment(C)

        matches = []
        for r, c in zip(row_ind, col_ind):
            if C[r, c] < 2.0:  # 代价阈值
                matches.append((r, c))

        return matches
