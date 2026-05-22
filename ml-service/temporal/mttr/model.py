"""MTTR (Multi-Task Temporal Reasoning) 模型

多任务学习：同时预测关系类型 + 时间先后顺序
基于BERT的时序编码：对 (time_i, relation_i, time_j, relation_j) 做时序关系预测
"""
import torch
import torch.nn as nn
from transformers import AutoModel


class MTTRModel(nn.Module):
    """多任务时序推理模型"""

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        model_name = config.get("model_name", "bert-base-chinese")
        hidden_size = config.get("hidden_size", 768)
        num_relations = config.get("num_relations", 7)
        num_temporal = config.get("num_temporal", 4)  # before/after/overlap/simultaneous
        dropout = config.get("dropout", 0.1)

        self.bert = AutoModel.from_pretrained(model_name)

        # 关系分类头（多任务1）
        self.relation_head = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 2, num_relations),
        )

        # 时序关系分类头（多任务2）
        self.temporal_head = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, num_temporal),
        )

        # 时间编码层
        self.time_encoder = nn.Linear(1, hidden_size)

    def forward(self, input_ids_a, attention_mask_a,
                input_ids_b=None, attention_mask_b=None,
                relation_labels=None, temporal_labels=None):
        """
        Args:
            input_ids_a: (batch, seq_len) 四元组A的token
            attention_mask_a: (batch, seq_len)
            input_ids_b: (batch, seq_len) 四元组B的token (可选)
            relation_labels: (batch,) 关系标签
            temporal_labels: (batch,) 时序关系标签
        """
        # 编码四元组A
        out_a = self.bert(input_ids=input_ids_a, attention_mask=attention_mask_a)
        repr_a = out_a.last_hidden_state[:, 0, :]  # CLS token

        result = {}

        # 关系分类
        rel_logits = self.relation_head(repr_a)
        result["relation_logits"] = rel_logits

        if relation_labels is not None:
            loss_fn = nn.CrossEntropyLoss()
            result["relation_loss"] = loss_fn(rel_logits, relation_labels)

        # 时序关系分类（需要两个四元组）
        if input_ids_b is not None:
            out_b = self.bert(input_ids=input_ids_b, attention_mask=attention_mask_b)
            repr_b = out_b.last_hidden_state[:, 0, :]

            # 拼接两个表示
            combined = torch.cat([repr_a, repr_b], dim=-1)
            temp_logits = self.temporal_head(combined)
            result["temporal_logits"] = temp_logits

            if temporal_labels is not None:
                loss_fn = nn.CrossEntropyLoss()
                result["temporal_loss"] = loss_fn(temp_logits, temporal_labels)

        if "relation_loss" in result and "temporal_loss" in result:
            result["loss"] = result["relation_loss"] + 0.5 * result["temporal_loss"]

        return result
