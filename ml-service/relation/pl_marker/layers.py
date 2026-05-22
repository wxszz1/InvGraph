"""PL-Marker 实体span标注层 + 关系分类层

PL-Marker的核心思想：
1. 在输入序列中插入特殊标记 [E1] [/E1] [E2] [/E2] 来标注实体边界
2. 通过BERT编码后，用[E1]和[/E1]位置的隐状态预测实体类型
3. 用[E2]和[/E2]位置的隐状态做关系分类
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


class EntitySpanLayer(nn.Module):
    """实体span标注层：预测每个token是否为实体边界（SUBJ-H/SUBJ-T/OBJ-H/OBJ-T）"""

    def __init__(self, hidden_size: int, num_entity_types: int = 2):
        super().__init__()
        # subject head/tail + object head/tail 共4种标记
        self.num_tags = 4  # SUBJ-H, SUBJ-T, OBJ-H, OBJ-T
        self.classifier = nn.Linear(hidden_size, self.num_tags)

    def forward(self, hidden_states: torch.Tensor, attention_mask: torch.Tensor = None):
        """
        Args:
            hidden_states: (batch, seq_len, hidden_size)
            attention_mask: (batch, seq_len)
        Returns:
            logits: (batch, seq_len, num_tags)
        """
        return self.classifier(hidden_states)


class RelationClassifier(nn.Module):
    """关系分类层：对检测到的实体对进行关系分类"""

    def __init__(self, hidden_size: int, num_relations: int, dropout: float = 0.1):
        super().__init__()
        self.head_proj = nn.Linear(hidden_size, hidden_size)
        self.tail_proj = nn.Linear(hidden_size, hidden_size)
        self.classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(hidden_size * 2, hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, num_relations),
        )

    def forward(self, head_repr: torch.Tensor, tail_repr: torch.Tensor):
        """
        Args:
            head_repr: (batch, hidden_size) 头实体表示
            tail_repr: (batch, hidden_size) 尾实体表示
        Returns:
            logits: (batch, num_relations)
        """
        head = self.head_proj(head_repr)
        tail = self.tail_proj(tail_repr)
        combined = torch.cat([head, tail], dim=-1)
        return self.classifier(combined)


class EntityPooler(nn.Module):
    """从标记位置提取实体表示"""

    def __init__(self, hidden_size: int, pool_type: str = "marker"):
        super().__init__()
        self.pool_type = pool_type
        if pool_type == "attention":
            self.attn = nn.Linear(hidden_size, 1)

    def forward(self, hidden_states, marker_positions):
        """
        Args:
            hidden_states: (batch, seq_len, hidden)
            marker_positions: dict with 'head_start', 'head_end', 'tail_start', 'tail_end'
                              each is (batch,) tensor of positions
        Returns:
            head_repr, tail_repr: each (batch, hidden)
        """
        batch_size = hidden_states.size(0)
        batch_idx = torch.arange(batch_size, device=hidden_states.device)

        # 取head start和end位置的隐状态，做平均
        head_start = hidden_states[batch_idx, marker_positions["head_start"]]
        head_end = hidden_states[batch_idx, marker_positions["head_end"]]
        head_repr = (head_start + head_end) / 2

        tail_start = hidden_states[batch_idx, marker_positions["tail_start"]]
        tail_end = hidden_states[batch_idx, marker_positions["tail_end"]]
        tail_repr = (tail_start + tail_end) / 2

        return head_repr, tail_repr
