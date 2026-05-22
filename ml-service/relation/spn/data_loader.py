"""SPN 数据加载器"""
import json
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer

from ..data.config import RELATION2ID, TRAIN_CONFIG


class SPNDataset(Dataset):
    """SPN格式数据集"""

    def __init__(self, data_path: str, tokenizer_name: str = "bert-base-chinese",
                 max_len: int = 256):
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
        self.max_len = max_len
        self.data = []

        with open(data_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    self.data.append(json.loads(line))

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        sample = self.data[idx]
        text = sample.get("text", "")
        triple_set = sample.get("triple_set", [])

        # Tokenize
        encoding = self.tokenizer(
            text, max_length=self.max_len,
            padding="max_length", truncation=True,
            return_tensors="pt",
        )

        # 构建ground truth三元组（基于token位置）
        gt_triples = []
        input_text = self.tokenizer.decode(
            encoding["input_ids"][0], skip_special_tokens=True
        )

        for triple in triple_set:
            subj = triple["subject"]
            rel = triple["relation"]
            obj = triple["object"]
            rel_id = RELATION2ID.get(rel, len(RELATION2ID) - 1)

            # 在tokenized text中找位置
            subj_start = input_text.find(subj)
            obj_start = input_text.find(obj)

            if subj_start >= 0 and obj_start >= 0:
                # 字符位置近似为token位置
                gt_triples.append((
                    subj_start, subj_start + len(subj) - 1,
                    rel_id,
                    obj_start, obj_start + len(obj) - 1,
                ))

        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "gt_triples": gt_triples,
            "text": text,
            "triple_set": triple_set,
        }


def spn_collate_fn(batch):
    return {
        "input_ids": torch.stack([b["input_ids"] for b in batch]),
        "attention_mask": torch.stack([b["attention_mask"] for b in batch]),
        "gt_triples": [b["gt_triples"] for b in batch],
        "text": [b["text"] for b in batch],
        "triple_set": [b["triple_set"] for b in batch],
    }


def get_spn_dataloader(data_path: str, batch_size: int = None, shuffle: bool = True):
    if batch_size is None:
        batch_size = TRAIN_CONFIG["batch_size"]
    dataset = SPNDataset(
        data_path,
        tokenizer_name=TRAIN_CONFIG["model_name"],
        max_len=TRAIN_CONFIG["max_seq_len"],
    )
    return DataLoader(
        dataset, batch_size=batch_size, shuffle=shuffle,
        collate_fn=spn_collate_fn, num_workers=0, pin_memory=True,
    )
