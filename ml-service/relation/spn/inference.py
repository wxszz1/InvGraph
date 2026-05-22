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

                    # 解码subject span（起止位置）
                    subj_start, subj_end = self._decode_span(subj_dist, encoding)
                    # 解码object span
                    obj_start, obj_end = self._decode_span(obj_dist, encoding)

                    # 从原始文本提取实体
                    subj_text = text[subj_start:subj_end] if subj_start < subj_end else ""
                    obj_text = text[obj_start:obj_end] if obj_start < obj_end else ""

                    if subj_text and obj_text:
                        triples.append({
                            "subject": subj_text,
                            "relation": rel_name,
                            "object": obj_text,
                            "confidence": round(max_prob.item(), 3),
                        })

        return triples

    def _decode_span(self, dist, encoding, threshold=0.3):
        """从位置概率分布解码实体span的起止位置"""
        probs = dist.cpu().numpy()
        # 找到概率 > threshold 的连续区间
        seq_len = encoding["attention_mask"][0].sum().item()
        high_prob_positions = [i for i in range(1, min(seq_len, len(probs))) if probs[i] > threshold]

        if not high_prob_positions:
            # fallback: 取argmax位置
            pos = dist.argmax().item()
            # 将token位置映射回字符位置
            offsets = encoding.offset_mapping[0].tolist()
            if pos < len(offsets) and offsets[pos] != (0, 0):
                return offsets[pos][0], offsets[pos][1]
            return 0, 0

        # 取连续区间的起止
        start_pos = high_prob_positions[0]
        end_pos = high_prob_positions[-1] + 1

        # 映射回原始文本的字符位置
        offsets = encoding.offset_mapping[0].tolist()
        if start_pos < len(offsets) and end_pos <= len(offsets):
            char_start = offsets[start_pos][0]
            char_end = offsets[end_pos - 1][1]
            return char_start, char_end

        return 0, 0

        return triples
