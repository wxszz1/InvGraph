"""SPN (Set Prediction Network) 模型

架构：
- Backbone: BERT-base-chinese
- N个query slot并行输出(subject, relation, object)
- 使用Transformer decoder layer做query-to-sequence attention
- 匈牙利匹配计算最优分配
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoModel


class SPNModel(nn.Module):
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        model_name = config.get("model_name", "bert-base-chinese")
        hidden_size = config.get("hidden_size", 768)
        num_relations = config.get("num_relations", 7)
        num_queries = config.get("num_queries", 30)
        dropout = config.get("dropout", 0.1)
        num_decoder_layers = config.get("num_decoder_layers", 3)

        # BERT backbone
        self.bert = AutoModel.from_pretrained(model_name)

        # Query slots (可学习参数)
        self.query_embed = nn.Embedding(num_queries, hidden_size)

        # Transformer decoder layers
        decoder_layer = nn.TransformerDecoderLayer(
            d_model=hidden_size, nhead=8,
            dim_feedforward=hidden_size * 4,
            dropout=dropout, batch_first=True,
        )
        self.decoder = nn.TransformerDecoder(decoder_layer, num_decoder_layers)

        # 预测头
        # 关系分类
        self.relation_head = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, num_relations),
        )

        # Subject位置预测
        self.subj_head = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
        )

        # Object位置预测
        self.obj_head = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
        )

    def forward(self, input_ids, attention_mask, token_type_ids=None):
        """
        Args:
            input_ids: (batch, seq_len)
            attention_mask: (batch, seq_len)
        Returns:
            pred_scores: (batch, num_queries, num_relations)
            pred_subj: (batch, num_queries, seq_len)
            pred_obj: (batch, num_queries, seq_len)
        """
        batch_size = input_ids.size(0)
        seq_len = input_ids.size(1)

        # BERT编码
        bert_out = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
        )
        memory = bert_out.last_hidden_state  # (batch, seq_len, hidden)

        # Query slots
        queries = self.query_embed.weight.unsqueeze(0).expand(batch_size, -1, -1)
        # (batch, num_queries, hidden)

        # Decoder: query attend to sequence
        tgt_mask = None
        memory_key_padding_mask = (attention_mask == 0)
        decoded = self.decoder(
            tgt=queries,
            memory=memory,
            memory_key_padding_mask=memory_key_padding_mask,
        )  # (batch, num_queries, hidden)

        # 关系分类
        pred_scores = self.relation_head(decoded)  # (batch, Q, R)

        # 实体位置预测
        subj_feat = self.subj_head(decoded)  # (batch, Q, hidden)
        obj_feat = self.obj_head(decoded)     # (batch, Q, hidden)

        # 与序列token做点积，得到位置分布
        memory_proj = memory.transpose(1, 2)  # (batch, hidden, seq_len)
        pred_subj = torch.bmm(subj_feat, memory_proj)  # (batch, Q, seq_len)
        pred_obj = torch.bmm(obj_feat, memory_proj)    # (batch, Q, seq_len)

        return {
            "pred_scores": pred_scores,
            "pred_subj": pred_subj,
            "pred_obj": pred_obj,
        }
