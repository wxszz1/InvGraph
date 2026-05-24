"""训练 MTTR (Multi-Task Temporal Reasoning) 模型

双任务训练：
1. 关系分类：四元组 → 关系类型 (7类)
2. 时序关系分类：四元组对 → 时序关系 (4类: before/after/overlap/simultaneous)
"""
import os
import sys
import json
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer
import numpy as np

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from temporal.mttr.model import MTTRModel

# 超参（与关系抽取模型保持一致）
CONFIG = {
    "model_name": "bert-base-chinese",
    "max_seq_len": 128,
    "batch_size": 16,
    "learning_rate": 2e-5,
    "epochs": 5,
    "warmup_ratio": 0.1,
    "weight_decay": 0.01,
    "max_grad_norm": 1.0,
    "seed": 42,
    "hidden_size": 768,
    "num_relations": 7,
    "num_temporal": 4,
    "dropout": 0.1,
}

DATA_DIR = os.path.join(BASE_DIR, "data", "mttr")


class MTTRDataset(Dataset):
    """MTTR训练数据集"""

    def __init__(self, data_path, tokenizer, max_len, mode="relation"):
        self.tokenizer = tokenizer
        self.max_len = max_len
        self.mode = mode
        self.samples = []

        with open(data_path, 'r', encoding='utf-8') as f:
            for line in f:
                item = json.loads(line.strip())
                if mode == "relation":
                    self.samples.append({
                        "text": item["text"],
                        "relation_label": item["relation_label"],
                    })
                elif mode == "temporal":
                    self.samples.append({
                        "text_a": item["text_a"],
                        "text_b": item["text_b"],
                        "temporal_label": item["temporal_label"],
                    })

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        item = self.samples[idx]
        if self.mode == "relation":
            enc = self.tokenizer(
                item["text"], max_length=self.max_len,
                padding="max_length", truncation=True,
                return_tensors="pt"
            )
            return {
                "input_ids_a": enc["input_ids"].squeeze(0),
                "attention_mask_a": enc["attention_mask"].squeeze(0),
                "relation_labels": torch.tensor(item["relation_label"], dtype=torch.long),
            }
        else:  # temporal
            enc_a = self.tokenizer(
                item["text_a"], max_length=self.max_len,
                padding="max_length", truncation=True,
                return_tensors="pt"
            )
            enc_b = self.tokenizer(
                item["text_b"], max_length=self.max_len,
                padding="max_length", truncation=True,
                return_tensors="pt"
            )
            return {
                "input_ids_a": enc_a["input_ids"].squeeze(0),
                "attention_mask_a": enc_a["attention_mask"].squeeze(0),
                "input_ids_b": enc_b["input_ids"].squeeze(0),
                "attention_mask_b": enc_b["attention_mask"].squeeze(0),
                "temporal_labels": torch.tensor(item["temporal_label"], dtype=torch.long),
            }


def train(model_dir):
    """训练MTTR模型，保存到model_dir"""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[MTTR] Device: {device}", flush=True)

    # 加载tokenizer
    tokenizer = AutoTokenizer.from_pretrained(CONFIG["model_name"])

    # 加载数据
    rel_train_path = os.path.join(DATA_DIR, "rel_train.jsonl")
    rel_val_path = os.path.join(DATA_DIR, "rel_val.jsonl")
    temp_train_path = os.path.join(DATA_DIR, "temp_train.jsonl")
    temp_val_path = os.path.join(DATA_DIR, "temp_val.jsonl")

    if not os.path.exists(rel_train_path):
        raise FileNotFoundError(f"关系训练数据不存在: {rel_train_path}，请先运行 gen_data.py")

    rel_train_ds = MTTRDataset(rel_train_path, tokenizer, CONFIG["max_seq_len"], mode="relation")
    rel_val_ds = MTTRDataset(rel_val_path, tokenizer, CONFIG["max_seq_len"], mode="relation") if os.path.exists(rel_val_path) else None
    temp_train_ds = MTTRDataset(temp_train_path, tokenizer, CONFIG["max_seq_len"], mode="temporal")
    temp_val_ds = MTTRDataset(temp_val_path, tokenizer, CONFIG["max_seq_len"], mode="temporal") if os.path.exists(temp_val_path) else None

    rel_loader = DataLoader(rel_train_ds, batch_size=CONFIG["batch_size"], shuffle=True)
    temp_loader = DataLoader(temp_train_ds, batch_size=CONFIG["batch_size"], shuffle=True)

    print(f"[MTTR] Relation samples: {len(rel_train_ds)}, Temporal samples: {len(temp_train_ds)}", flush=True)

    # 初始化模型
    model = MTTRModel(CONFIG).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=CONFIG["learning_rate"],
                                   weight_decay=CONFIG["weight_decay"])

    # 学习率调度
    total_steps = max(len(rel_loader), len(temp_loader)) * CONFIG["epochs"]
    warmup_steps = int(total_steps * CONFIG["warmup_ratio"])

    def lr_lambda(step):
        if step < warmup_steps:
            return step / max(warmup_steps, 1)
        return max(0.0, (total_steps - step) / max(total_steps - warmup_steps, 1))

    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)

    # 训练循环
    best_val_loss = float("inf")
    os.makedirs(model_dir, exist_ok=True)

    for epoch in range(CONFIG["epochs"]):
        model.train()
        rel_loss_sum = 0
        temp_loss_sum = 0
        rel_batches = 0
        temp_batches = 0

        # 交替训练两个任务
        temp_iter = iter(temp_loader)
        for rel_batch in rel_loader:
            # 关系分类
            rel_batch = {k: v.to(device) for k, v in rel_batch.items()}
            rel_out = model(
                input_ids_a=rel_batch["input_ids_a"],
                attention_mask_a=rel_batch["attention_mask_a"],
                relation_labels=rel_batch["relation_labels"],
            )
            rel_loss = rel_out["relation_loss"]

            # 时序分类（取一个batch）
            try:
                temp_batch = next(temp_iter)
            except StopIteration:
                temp_iter = iter(temp_loader)
                temp_batch = next(temp_iter)

            temp_batch = {k: v.to(device) for k, v in temp_batch.items()}
            temp_out = model(
                input_ids_a=temp_batch["input_ids_a"],
                attention_mask_a=temp_batch["attention_mask_a"],
                input_ids_b=temp_batch["input_ids_b"],
                attention_mask_b=temp_batch["attention_mask_b"],
                temporal_labels=temp_batch["temporal_labels"],
            )
            temp_loss = temp_out["temporal_loss"]

            # 联合损失
            loss = rel_loss + 0.5 * temp_loss

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), CONFIG["max_grad_norm"])
            optimizer.step()
            scheduler.step()

            rel_loss_sum += rel_loss.item()
            temp_loss_sum += temp_loss.item()
            rel_batches += 1
            temp_batches += 1

        avg_rel_loss = rel_loss_sum / max(rel_batches, 1)
        avg_temp_loss = temp_loss_sum / max(temp_batches, 1)

        # 验证
        val_info = ""
        if rel_val_ds:
            val_rel_loss = _eval(model, rel_val_ds, device, mode="relation")
            val_info += f" val_rel={val_rel_loss:.4f}"
        if temp_val_ds:
            val_temp_loss = _eval(model, temp_val_ds, device, mode="temporal")
            val_info += f" val_temp={val_temp_loss:.4f}"

        print(f"  Epoch {epoch+1}/{CONFIG['epochs']}: "
              f"rel_loss={avg_rel_loss:.4f} temp_loss={avg_temp_loss:.4f}{val_info}", flush=True)

        # 保存 best model
        total_val = 0
        if rel_val_ds:
            total_val += _eval(model, rel_val_ds, device, mode="relation")
        if temp_val_ds:
            total_val += 0.5 * _eval(model, temp_val_ds, device, mode="temporal")

        if total_val < best_val_loss:
            best_val_loss = total_val
            save_path = os.path.join(model_dir, "best_model.bin")
            torch.save({
                "model_state_dict": model.state_dict(),
                "config": CONFIG,
            }, save_path)
            print(f"    -> Saved best model (val_loss={total_val:.4f})", flush=True)

    # 保存 final model
    final_path = os.path.join(model_dir, "final_model.bin")
    torch.save({
        "model_state_dict": model.state_dict(),
        "config": CONFIG,
    }, final_path)
    print(f"[MTTR] Training complete. Best val_loss={best_val_loss:.4f}", flush=True)
    print(f"[MTTR] Model saved to {model_dir}", flush=True)


def _eval(model, dataset, device, mode="relation"):
    """验证集评估"""
    model.eval()
    loader = DataLoader(dataset, batch_size=CONFIG["batch_size"])
    total_loss = 0
    n = 0
    with torch.no_grad():
        for batch in loader:
            batch = {k: v.to(device) for k, v in batch.items()}
            if mode == "relation":
                out = model(
                    input_ids_a=batch["input_ids_a"],
                    attention_mask_a=batch["attention_mask_a"],
                    relation_labels=batch["relation_labels"],
                )
                total_loss += out["relation_loss"].item()
            else:
                out = model(
                    input_ids_a=batch["input_ids_a"],
                    attention_mask_a=batch["attention_mask_a"],
                    input_ids_b=batch["input_ids_b"],
                    attention_mask_b=batch["attention_mask_b"],
                    temporal_labels=batch["temporal_labels"],
                )
                total_loss += out["temporal_loss"].item()
            n += 1
    model.train()
    return total_loss / max(n, 1)


if __name__ == "__main__":
    model_dir = os.path.join(BASE_DIR, "models", "mttr")
    train(model_dir)
