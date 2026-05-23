"""PL-Marker 训练脚本

支持：
- fp16混合精度训练（PyTorch AMP）
- gradient accumulation
- warmup + cosine decay
- checkpoint保存
"""
import os
import sys
import time
import torch
import torch.nn as nn
from torch.cuda.amp import GradScaler, autocast
from torch.optim import AdamW
from transformers import get_cosine_schedule_with_warmup

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from relation.pl_marker.model import PLMarkerModel
from relation.pl_marker.data_loader import get_dataloader
from relation.data.config import TRAIN_CONFIG, RELATION2ID, MODEL_DIR


def train(train_data_path: str, val_data_path: str = None, save_dir: str = None):
    """训练PL-Marker模型"""
    config = TRAIN_CONFIG
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if save_dir is None:
        save_dir = os.path.join(BASE_DIR, MODEL_DIR, "pl_marker")
    os.makedirs(save_dir, exist_ok=True)

    print(f"训练设备: {device}")
    if device.type == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        total = getattr(torch.cuda.get_device_properties(0), 'total_memory', None)
        if total:
            print(f"显存: {total / 1024**3:.1f} GB")

    # 初始化模型
    model_config = {
        "model_name": config["model_name"],
        "hidden_size": 768,
        "num_relations": len(RELATION2ID) + 1,  # +1 for None
        "dropout": 0.1,
    }
    model = PLMarkerModel(model_config)

    # 数据加载（先加载数据，因为data_loader会添加特殊token到tokenizer）
    print(f"加载训练数据: {train_data_path}")
    train_loader = get_dataloader(train_data_path, config["batch_size"], shuffle=True)

    # resize BERT embeddings以包含[E1]/[/E1]/[E2]/[/E2]等特殊token
    new_vocab_size = len(train_loader.dataset.tokenizer)
    if new_vocab_size != model.bert.config.vocab_size:
        model.bert.resize_token_embeddings(new_vocab_size)
        print(f"Embeddings resized: {model.bert.config.vocab_size} -> {new_vocab_size}")

    model.to(device)

    val_loader = None
    if val_data_path and os.path.exists(val_data_path):
        val_loader = get_dataloader(val_data_path, config["batch_size"], shuffle=False)

    # 优化器和学习率调度
    no_decay = ["bias", "LayerNorm.weight"]
    optimizer_grouped_parameters = [
        {
            "params": [p for n, p in model.named_parameters()
                       if not any(nd in n for nd in no_decay) and p.requires_grad],
            "weight_decay": config["weight_decay"],
        },
        {
            "params": [p for n, p in model.named_parameters()
                       if any(nd in n for nd in no_decay) and p.requires_grad],
            "weight_decay": 0.0,
        },
    ]
    optimizer = AdamW(optimizer_grouped_parameters, lr=config["learning_rate"])

    total_steps = len(train_loader) * config["epochs"] // config["gradient_accumulation_steps"]
    warmup_steps = int(total_steps * config["warmup_ratio"])
    scheduler = get_cosine_schedule_with_warmup(optimizer, warmup_steps, total_steps)

    # fp16
    scaler = GradScaler(enabled=config["fp16"] and device.type == "cuda")

    print(f"总训练步数: {total_steps}, warmup: {warmup_steps}")
    print(f"fp16: {config['fp16']}, gradient_accumulation: {config['gradient_accumulation_steps']}")

    # 训练循环
    best_val_loss = float('inf')
    global_step = 0

    for epoch in range(config["epochs"]):
        model.train()
        epoch_loss = 0
        epoch_steps = 0
        t0 = time.time()

        for step, batch in enumerate(train_loader):
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            entity_positions = {k: v.to(device) for k, v in batch["entity_positions"].items()}
            rel_label = batch["rel_label"].to(device)

            with autocast(enabled=config["fp16"] and device.type == "cuda"):
                outputs = model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    entity_positions=entity_positions,
                    relation_labels=rel_label,
                )
                loss = outputs.get("loss", torch.tensor(0.0, device=device))
                loss = loss / config["gradient_accumulation_steps"]

            scaler.scale(loss).backward()

            if (step + 1) % config["gradient_accumulation_steps"] == 0:
                scaler.unscale_(optimizer)
                nn.utils.clip_grad_norm_(model.parameters(), config["max_grad_norm"])
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad()
                scheduler.step()
                global_step += 1

            epoch_loss += loss.item() * config["gradient_accumulation_steps"]
            epoch_steps += 1

        avg_loss = epoch_loss / max(epoch_steps, 1)
        elapsed = time.time() - t0
        lr = scheduler.get_last_lr()[0]

        msg = f"Epoch {epoch+1}/{config['epochs']} | loss: {avg_loss:.4f} | lr: {lr:.2e} | time: {elapsed:.1f}s"

        # 验证
        if val_loader:
            val_loss = evaluate_loss(model, val_loader, device, config["fp16"])
            msg += f" | val_loss: {val_loss:.4f}"
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                save_model(model, save_dir, "best_model")
                msg += " [SAVED]"

        print(msg)

        # 每5个epoch保存
        if (epoch + 1) % 5 == 0:
            save_model(model, save_dir, f"epoch_{epoch+1}")

    save_model(model, save_dir, "final_model")
    print(f"\n训练完成！最佳验证loss: {best_val_loss:.4f}")
    return model


def evaluate_loss(model, data_loader, device, use_fp16=False):
    """计算验证集loss"""
    model.eval()
    total_loss = 0
    count = 0
    with torch.no_grad():
        for batch in data_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            entity_positions = {k: v.to(device) for k, v in batch["entity_positions"].items()}
            rel_label = batch["rel_label"].to(device)

            with autocast(enabled=use_fp16 and device.type == "cuda"):
                outputs = model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    entity_positions=entity_positions,
                    relation_labels=rel_label,
                )
                loss = outputs.get("loss", torch.tensor(0.0))
            total_loss += loss.item()
            count += 1

    return total_loss / max(count, 1)


def save_model(model, save_dir, name="best_model"):
    """保存模型checkpoint"""
    path = os.path.join(save_dir, f"{name}.bin")
    torch.save({
        "model_state_dict": model.state_dict(),
        "config": model.config,
    }, path)
    print(f"模型已保存: {path}")


def load_model(model_path: str, device: str = "cuda"):
    """加载模型checkpoint"""
    device = torch.device(device if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(model_path, map_location=device)
    model = PLMarkerModel(checkpoint["config"])
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()
    return model


if __name__ == "__main__":
    data_dir = os.path.join(BASE_DIR, "data", "pl_marker")
    train_path = os.path.join(data_dir, "train.jsonl")
    val_path = os.path.join(data_dir, "val.jsonl")

    if not os.path.exists(train_path):
        print(f"训练数据不存在: {train_path}")
        print("请先运行 data/preprocess.py 生成训练数据")
        sys.exit(1)

    train(train_path, val_path)
