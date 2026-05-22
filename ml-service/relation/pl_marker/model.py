"""PL-Marker 模型定义

架构：
- Backbone: BERT-base-chinese
- 实体识别: EntitySpanLayer（预测SUBJ-H/T, OBJ-H/T）
- 关系分类: RelationClassifier（对实体对做关系分类）
- 使用fp16混合精度训练
"""
import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer

from .layers import EntitySpanLayer, RelationClassifier, EntityPooler


class PLMarkerModel(nn.Module):
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        model_name = config.get("model_name", "bert-base-chinese")
        hidden_size = config.get("hidden_size", 768)
        num_relations = config.get("num_relations", 7)
        dropout = config.get("dropout", 0.1)

        # BERT backbone
        self.bert = AutoModel.from_pretrained(model_name)

        # 实体span标注层
        self.entity_span = EntitySpanLayer(hidden_size, num_entity_types=2)

        # 实体池化
        self.entity_pooler = EntityPooler(hidden_size)

        # 关系分类层
        self.relation_classifier = RelationClassifier(
            hidden_size, num_relations, dropout
        )

    def forward(self, input_ids, attention_mask, token_type_ids=None,
                entity_positions=None, relation_labels=None):
        """
        Args:
            input_ids: (batch, seq_len)
            attention_mask: (batch, seq_len)
            entity_positions: dict of marker positions (optional, for training)
            relation_labels: (batch, num_relations) 真实标签 (optional, for training)
        Returns:
            dict with 'entity_logits', 'relation_logits', 'loss'
        """
        # BERT编码
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
        )
        hidden_states = outputs.last_hidden_state  # (batch, seq_len, hidden)

        # 实体span标注
        entity_logits = self.entity_span(hidden_states, attention_mask)
        # (batch, seq_len, 4)

        result = {"entity_logits": entity_logits, "hidden_states": hidden_states}

        # 如果提供了实体位置，做关系分类
        if entity_positions is not None:
            head_repr, tail_repr = self.entity_pooler(
                hidden_states, entity_positions
            )
            relation_logits = self.relation_classifier(head_repr, tail_repr)
            result["relation_logits"] = relation_logits

            # 计算损失
            if relation_labels is not None:
                loss_fn = nn.CrossEntropyLoss()
                relation_loss = loss_fn(relation_logits, relation_labels)
                result["loss"] = relation_loss

        return result

    def get_bert_embeddings(self, input_ids):
        """获取BERT词嵌入"""
        return self.bert.embeddings(input_ids)
