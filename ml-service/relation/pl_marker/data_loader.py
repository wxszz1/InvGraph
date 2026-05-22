"""PL-Marker 数据加载器

将PL-Marker格式数据转换为模型输入：
1. 字符级tokenize
2. 插入实体标记 [E1]/[/E1] [E2]/[/E2]
3. 截断/填充到max_seq_len
4. 生成entity_positions和relation_labels
"""
import json
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer

from ..data.config import RELATION2ID, TRAIN_CONFIG


# 实体标记token
MARKER_TOKENS = ["[E1]", "[/E1]", "[E2]", "[/E2]"]


class PLMarkerDataset(Dataset):
    """PL-Marker格式数据集"""

    def __init__(self, data_path: str, tokenizer_name: str = "bert-base-chinese",
                 max_len: int = 256):
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
        self.max_len = max_len
        self.data = []

        # 添加标记token到tokenizer
        self.tokenizer.add_special_tokens(
            {"additional_special_tokens": MARKER_TOKENS}
        )

        with open(data_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    self.data.append(json.loads(line))

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        sample = self.data[idx]
        tokens = sample["tokens"]
        entities = sample.get("entities", [])
        relations = sample.get("relations", [])

        # 选择一对实体进行训练（如果有多个关系，随机选一个）
        if not entities or len(entities) < 2:
            return self._empty_sample()

        # 选择一个关系来训练
        if relations:
            rel = relations[0]  # 简化：取第一个关系
            head_idx = rel["head"]
            tail_idx = rel["tail"]
            rel_type = rel["type"]
            rel_label = RELATION2ID.get(rel_type, 0)
        else:
            # 无关系：选两个随机实体，标签为None关系
            head_idx = 0
            tail_idx = min(1, len(entities) - 1)
            rel_label = len(RELATION2ID)  # "None"类

        if head_idx >= len(entities) or tail_idx >= len(entities):
            return self._empty_sample()

        head_ent = entities[head_idx]
        tail_ent = entities[tail_idx]

        # 构建带标记的序列
        marked_tokens = self._insert_markers(tokens, head_ent, tail_ent)

        # Tokenize
        encoding = self.tokenizer(
            marked_tokens,
            is_split_into_words=True,
            max_length=self.max_len,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

        # 找到标记位置
        marker_positions = self._find_marker_positions(encoding)

        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "marker_positions": marker_positions,
            "rel_label": torch.tensor(rel_label, dtype=torch.long),
        }

    def _insert_markers(self, tokens, head_ent, tail_ent):
        """在token序列中插入实体标记"""
        marked = []
        head_start = head_ent["start"]
        head_end = head_ent["end"]
        tail_start = tail_ent["start"]
        tail_end = tail_ent["end"]

        for i, tok in enumerate(tokens):
            if i == head_start:
                marked.append("[E1]")
            if i == tail_start:
                marked.append("[E2]")
            marked.append(tok)
            if i == head_end - 1:
                marked.append("[/E1]")
            if i == tail_end - 1:
                marked.append("[/E2]")

        return marked

    def _find_marker_positions(self, encoding):
        """找到标记token在编码后的位置"""
        input_ids = encoding["input_ids"].squeeze(0).tolist()
        e1_id = self.tokenizer.convert_tokens_to_ids("[E1]")
        e1_end_id = self.tokenizer.convert_tokens_to_ids("[/E1]")
        e2_id = self.tokenizer.convert_tokens_to_ids("[E2]")
        e2_end_id = self.tokenizer.convert_tokens_to_ids("[/E2]")

        positions = {
            "head_start": 0, "head_end": 0,
            "tail_start": 0, "tail_end": 0,
        }
        for i, tid in enumerate(input_ids):
            if tid == e1_id:
                positions["head_start"] = i
            elif tid == e1_end_id:
                positions["head_end"] = i
            elif tid == e2_id:
                positions["tail_start"] = i
            elif tid == e2_end_id:
                positions["tail_end"] = i

        return positions

    def _empty_sample(self):
        """返回空样本（padding）"""
        encoding = self.tokenizer(
            "", max_length=self.max_len, padding="max_length",
            truncation=True, return_tensors="pt"
        )
        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "marker_positions": {
                "head_start": 0, "head_end": 0,
                "tail_start": 0, "tail_end": 0,
            },
            "rel_label": torch.tensor(len(RELATION2ID), dtype=torch.long),
        }


def collate_fn(batch):
    """自定义collate函数"""
    return {
        "input_ids": torch.stack([b["input_ids"] for b in batch]),
        "attention_mask": torch.stack([b["attention_mask"] for b in batch]),
        "entity_positions": {
            k: torch.tensor([b["marker_positions"][k] for b in batch], dtype=torch.long)
            for k in ["head_start", "head_end", "tail_start", "tail_end"]
        },
        "rel_label": torch.stack([b["rel_label"] for b in batch]),
    }


def get_dataloader(data_path: str, batch_size: int = None, shuffle: bool = True):
    """创建DataLoader"""
    if batch_size is None:
        batch_size = TRAIN_CONFIG["batch_size"]
    dataset = PLMarkerDataset(
        data_path,
        tokenizer_name=TRAIN_CONFIG["model_name"],
        max_len=TRAIN_CONFIG["max_seq_len"],
    )
    return DataLoader(
        dataset, batch_size=batch_size, shuffle=shuffle,
        collate_fn=collate_fn, num_workers=0, pin_memory=True,
    )
