"""SPN 训练脚本"""
import os
import sys
import time
import torch
from torch.cuda.amp import GradScaler, autocast
from torch.optim import AdamW
from transformers import get_cosine_schedule_with_warmup

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from relation.spn.model import SPNModel
from relation.spn.matcher import HungarianMatcher
from relation.spn.loss import SetPredictionLoss
from relation.spn.data_loader import get_spn_dataloader
from relation.data.config import TRAIN_CONFIG, RELATION2ID, MODEL_DIR


def train(train_data_path: str, val_data_path: str = None, save_dir: str = None):
    config = TRAIN_CONFIG
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if save_dir is None:
        save_dir = os.path.join(BASE_DIR, MODEL_DIR, "spn")
    os.makedirs(save_dir, exist_ok=True)

    print(f"SPN训练 | 设备: {device}")

    model_config = {
        "model_name": config["model_name"],
        "hidden_size": 768,
        "num_relations": len(RELATION2ID) + 1,
        "num_queries": 30,
        "dropout": 0.1,
        "num_decoder_layers": 3,
    }
    model = SPNModel(model_config)
    model.to(device)

    matcher = HungarianMatcher(cost_class=1.0, cost_entity=1.0)
    criterion = SetPredictionLoss(
        num_relations=len(RELATION2ID) + 1, num_queries=30
    )
    criterion.to(device)

    print(f"加载训练数据: {train_data_path}")
    train_loader = get_spn_dataloader(train_data_path, config["batch_size"])

    optimizer = AdamW(model.parameters(), lr=config["learning_rate"],
                      weight_decay=config["weight_decay"])
    total_steps = len(train_loader) * config["epochs"] // config["gradient_accumulation_steps"]
    scheduler = get_cosine_schedule_with_warmup(
        optimizer, int(total_steps * config["warmup_ratio"]), total_steps
    )
    scaler = GradScaler(enabled=config["fp16"] and device.type == "cuda")

    print(f"总步数: {total_steps}")

    for epoch in range(config["epochs"]):
        model.train()
        epoch_loss = 0
        t0 = time.time()

        for step, batch in enumerate(train_loader):
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            gt_triples_list = batch["gt_triples"]

            with autocast(enabled=config["fp16"] and device.type == "cuda"):
                outputs = model(input_ids=input_ids, attention_mask=attention_mask)

                # 对batch中每个样本做匹配和损失计算
                batch_loss = torch.tensor(0.0, device=device)
                for i in range(input_ids.size(0)):
                    gt = gt_triples_list[i]
                    matches = matcher(
                        outputs["pred_scores"][i],
                        outputs["pred_subj"][i],
                        outputs["pred_obj"][i],
                        gt,
                    )
                    loss_i, _ = criterion(
                        outputs["pred_scores"][i],
                        outputs["pred_subj"][i],
                        outputs["pred_obj"][i],
                        gt, matches,
                    )
                    batch_loss = batch_loss + loss_i

                batch_loss = batch_loss / input_ids.size(0) / config["gradient_accumulation_steps"]

            scaler.scale(batch_loss).backward()
            if (step + 1) % config["gradient_accumulation_steps"] == 0:
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), config["max_grad_norm"])
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad()
                scheduler.step()

            epoch_loss += batch_loss.item() * config["gradient_accumulation_steps"]

        avg_loss = epoch_loss / max(len(train_loader), 1)
        print(f"Epoch {epoch+1}/{config['epochs']} | loss: {avg_loss:.4f} | time: {time.time()-t0:.1f}s")

        if (epoch + 1) % 5 == 0:
            path = os.path.join(save_dir, f"epoch_{epoch+1}.bin")
            torch.save({"model_state_dict": model.state_dict(), "config": model_config}, path)

    path = os.path.join(save_dir, "best_model.bin")
    torch.save({"model_state_dict": model.state_dict(), "config": model_config}, path)
    print(f"SPN训练完成！模型保存: {path}")


if __name__ == "__main__":
    data_dir = os.path.join(BASE_DIR, "data", "spn")
    train_path = os.path.join(data_dir, "train.jsonl")
    if not os.path.exists(train_path):
        print(f"训练数据不存在: {train_path}")
        sys.exit(1)
    train(train_path)
