"""SPN 评估脚本"""
import os
import sys
import torch
from torch.cuda.amp import autocast

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from relation.spn.data_loader import get_spn_dataloader
from relation.data.config import ID2RELATION


def evaluate(model, test_data_path: str, batch_size: int = 16, threshold: float = 0.5):
    device = next(model.parameters()).device
    model.eval()

    loader = get_spn_dataloader(test_data_path, batch_size, shuffle=False)

    total_pred = 0
    total_gold = 0
    total_correct = 0

    with torch.no_grad():
        for batch in loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            gt_triples_list = batch["gt_triples"]
            gold_triples = batch["triple_set"]

            with autocast(enabled=device.type == "cuda"):
                outputs = model(input_ids=input_ids, attention_mask=attention_mask)

            for i in range(input_ids.size(0)):
                gold = gold_triples[i]
                total_gold += len(gold)

                # 从SPN输出解码预测
                scores = outputs["pred_scores"][i].softmax(-1)
                for q in range(scores.size(0)):
                    max_prob, rel_id = scores[q].max(-1)
                    if max_prob > threshold and rel_id.item() < len(ID2RELATION):
                        total_pred += 1
                        # 简化：只要关系正确就算正确
                        rel_name = ID2RELATION.get(rel_id.item(), "")
                        if any(t["relation"] == rel_name for t in gold):
                            total_correct += 1

    precision = total_correct / max(total_pred, 1)
    recall = total_correct / max(total_gold, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-8)

    print(f"\n=== SPN评估 ===")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1:        {f1:.4f}")

    return {"precision": precision, "recall": recall, "f1": f1}
