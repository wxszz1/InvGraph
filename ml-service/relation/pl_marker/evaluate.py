"""PL-Marker 评估脚本（F1/P/R）"""
import os
import sys
import torch
from torch.cuda.amp import autocast
import numpy as np
from sklearn.metrics import precision_recall_fscore_support, classification_report

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from relation.pl_marker.data_loader import get_dataloader
from relation.data.config import RELATION2ID, ID2RELATION


def evaluate(model, test_data_path: str, batch_size: int = 16):
    """评估模型在测试集上的表现"""
    device = next(model.parameters()).device
    model.eval()

    test_loader = get_dataloader(test_data_path, batch_size, shuffle=False)

    all_preds = []
    all_labels = []

    with torch.no_grad():
        for batch in test_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            entity_positions = {k: v.to(device) for k, v in batch["entity_positions"].items()}
            rel_label = batch["rel_label"].to(device)

            with autocast(enabled=device.type == "cuda"):
                outputs = model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    entity_positions=entity_positions,
                )

            if "relation_logits" in outputs:
                preds = outputs["relation_logits"].argmax(dim=-1).cpu().numpy()
                labels = rel_label.cpu().numpy()
                all_preds.extend(preds.tolist())
                all_labels.extend(labels.tolist())

    if not all_preds:
        print("无评估数据")
        return {}

    # 计算指标
    num_classes = len(RELATION2ID) + 1
    target_names = [ID2RELATION.get(i, f"Class_{i}") for i in range(num_classes)]

    # 过滤掉None类（最后一类）
    valid_mask = [l < len(RELATION2ID) for l in all_labels]
    filtered_preds = [p for p, m in zip(all_preds, valid_mask) if m]
    filtered_labels = [l for l, m in zip(all_labels, valid_mask) if m]

    if not filtered_preds:
        print("无有效关系预测")
        return {"accuracy": 0, "precision": 0, "recall": 0, "f1": 0}

    accuracy = sum(p == l for p, l in zip(all_preds, all_labels)) / len(all_preds)
    precision, recall, f1, _ = precision_recall_fscore_support(
        filtered_labels, filtered_preds, average="macro", zero_division=0
    )

    results = {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }

    print(f"\n=== 评估结果 ===")
    print(f"Accuracy:  {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1 Score:  {f1:.4f}")

    # 每类详细报告
    print(f"\n分类报告:")
    print(classification_report(
        filtered_labels, filtered_preds,
        target_names=[ID2RELATION.get(i, f"Class_{i}") for i in range(len(RELATION2ID))],
        zero_division=0,
    ))

    return results
