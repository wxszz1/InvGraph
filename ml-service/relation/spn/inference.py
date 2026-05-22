"""SPN 推理接口"""
import os
import sys
import torch
from transformers import AutoTokenizer
from torch.cuda.amp import autocast

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from relation.spn.model import SPNModel
from relation.data.config import ID2RELATION, TRAIN_CONFIG


class SPNInference:
    """SPN推理器"""

    def __init__(self, model_path: str = None, device: str = "cuda"):
        self.device = torch.device(
            device if torch.cuda.is_available() else "cpu"
        )

        if model_path and os.path.exists(model_path):
            checkpoint = torch.load(model_path, map_location=self.device)
            model_config = checkpoint.get("config", {
                "model_name": "bert-base-chinese",
                "hidden_size": 768,
                "num_relations": len(ID2RELATION) + 1,
                "num_queries": 30,
                "dropout": 0.1,
                "num_decoder_layers": 3,
            })
            self.model = SPNModel(model_config)
            self.model.load_state_dict(checkpoint["model_state_dict"])
            self.model.to(self.device)
            self.model.eval()
            self.has_model = True
        else:
            self.model = None
            self.has_model = False

        self.tokenizer = AutoTokenizer.from_pretrained(TRAIN_CONFIG["model_name"])

    def predict(self, text: str, threshold: float = 0.5) -> list:
        """
        给定文本，直接预测三元组集合（端到端）

        Args:
            text: 输入文本
            threshold: 置信度阈值
        Returns:
            triples: [{"subject": "...", "relation": "...", "object": "..."}, ...]
        """
        if not self.has_model:
            return []

        encoding = self.tokenizer(
            text, max_length=TRAIN_CONFIG["max_seq_len"],
            padding="max_length", truncation=True,
            return_tensors="pt",
        )

        input_ids = encoding["input_ids"].to(self.device)
        attention_mask = encoding["attention_mask"].to(self.device)

        with torch.no_grad():
            with autocast(enabled=self.device.type == "cuda"):
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                )

        triples = []
        scores = outputs["pred_scores"][0].softmax(-1)  # (Q, R)

        for q in range(scores.size(0)):
            max_prob, rel_id = scores[q].max(-1)
            if max_prob > threshold and rel_id.item() < len(ID2RELATION):
                rel_name = ID2RELATION.get(rel_id.item(), "")
                if rel_name and rel_name != "None":
                    # 从subject/object位置分布解码实体名
                    subj_dist = outputs["pred_subj"][0, q].softmax(-1)
                    obj_dist = outputs["pred_obj"][0, q].softmax(-1)

                    # 取概率最高的位置作为实体边界
                    subj_pos = subj_dist.argmax().item()
                    obj_pos = obj_dist.argmax().item()

                    # 简化：直接用位置附近的文本作为实体
                    triples.append({
                        "subject": text[max(0,subj_pos-2):subj_pos+3],
                        "relation": rel_name,
                        "object": text[max(0,obj_pos-2):obj_pos+3],
                        "confidence": round(max_prob.item(), 3),
                    })

        return triples
