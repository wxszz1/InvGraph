"""PL-Marker 推理接口

从文本中抽取实体和关系：
1. 对文本做NER获取实体候选
2. 对每对实体做关系分类
3. 返回三元组列表
"""
import os
import sys
import torch
from transformers import AutoTokenizer
from torch.cuda.amp import autocast

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from relation.pl_marker.model import PLMarkerModel
from relation.data.config import RELATION2ID, ID2RELATION, TRAIN_CONFIG

MARKER_TOKENS = ["[E1]", "[/E1]", "[E2]", "[/E2]"]


class PLMarkerInference:
    """PL-Marker推理器"""

    def __init__(self, model_path: str = None, device: str = "cuda"):
        self.device = torch.device(
            device if torch.cuda.is_available() else "cpu"
        )

        if model_path and os.path.exists(model_path):
            checkpoint = torch.load(model_path, map_location=self.device)
            model_config = checkpoint.get("config", {
                "model_name": "bert-base-chinese",
                "hidden_size": 768,
                "num_relations": len(RELATION2ID) + 1,
                "dropout": 0.1,
            })
            self.model = PLMarkerModel(model_config)
            self.model.load_state_dict(checkpoint["model_state_dict"])
            self.model.to(self.device)
            self.model.eval()
            self.has_model = True
        else:
            self.model = None
            self.has_model = False

        # Tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            TRAIN_CONFIG["model_name"]
        )
        self.tokenizer.add_special_tokens(
            {"additional_special_tokens": MARKER_TOKENS}
        )

    def predict(self, text: str, entities: list) -> list:
        """
        给定文本和实体列表，预测实体间的关系

        Args:
            text: 输入文本
            entities: 实体列表 [{"name": "...", "type": "...", "start": 0, "end": 3}, ...]
        Returns:
            relations: [{"head": "实体A", "relation": "INVEST", "tail": "实体B"}, ...]
        """
        if not self.has_model:
            return self._rule_based_fallback(text, entities)

        relations = []
        # 对每对实体做关系分类
        for i, head in enumerate(entities):
            for j, tail in enumerate(entities):
                if i == j:
                    continue

                # 构建带标记的输入
                tokens = list(text)
                marked = self._insert_markers(tokens, head, tail)

                encoding = self.tokenizer(
                    marked, is_split_into_words=True,
                    max_length=TRAIN_CONFIG["max_seq_len"],
                    padding="max_length", truncation=True,
                    return_tensors="pt",
                )

                input_ids = encoding["input_ids"].to(self.device)
                attention_mask = encoding["attention_mask"].to(self.device)

                marker_pos = self._find_marker_positions(input_ids[0])
                entity_positions = {k: torch.tensor([v], dtype=torch.long).to(self.device)
                                    for k, v in marker_pos.items()}

                with torch.no_grad():
                    with autocast(enabled=self.device.type == "cuda"):
                        outputs = self.model(
                            input_ids=input_ids,
                            attention_mask=attention_mask,
                            entity_positions=entity_positions,
                        )

                if "relation_logits" in outputs:
                    probs = torch.softmax(outputs["relation_logits"], dim=-1)
                    pred = probs.argmax(dim=-1).item()
                    conf = probs.max().item()

                    if pred < len(ID2RELATION) and conf > 0.5:
                        relations.append({
                            "head": head["name"],
                            "relation": ID2RELATION[pred],
                            "tail": tail["name"],
                            "confidence": round(conf, 3),
                        })

        return relations

    def _rule_based_fallback(self, text, entities):
        """模型未加载时的规则回退"""
        from ner.keywords import INVEST_KEYWORDS, LEAD_KEYWORDS
        relations = []
        investors = [e for e in entities if e.get("type") == "Investor"]
        enterprises = [e for e in entities if e.get("type") == "Enterprise"]

        for inv in investors:
            for ent in enterprises:
                for kw in LEAD_KEYWORDS:
                    if kw in text:
                        if inv["name"] in text and ent["name"] in text:
                            relations.append({
                                "head": inv["name"], "relation": "LEAD",
                                "tail": ent["name"], "confidence": 0.7,
                            })
                            break
                for kw in INVEST_KEYWORDS:
                    if kw in text:
                        if inv["name"] in text and ent["name"] in text:
                            if not any(r["head"] == inv["name"] and r["tail"] == ent["name"] for r in relations):
                                relations.append({
                                    "head": inv["name"], "relation": "INVEST",
                                    "tail": ent["name"], "confidence": 0.6,
                                })
                            break
        return relations

    def _insert_markers(self, tokens, head_ent, tail_ent):
        marked = []
        hs, he = head_ent.get("start", 0), head_ent.get("end", 0)
        ts, te = tail_ent.get("start", 0), tail_ent.get("end", 0)
        for i, tok in enumerate(tokens):
            if i == hs:
                marked.append("[E1]")
            if i == ts:
                marked.append("[E2]")
            marked.append(tok)
            if i == he - 1:
                marked.append("[/E1]")
            if i == te - 1:
                marked.append("[/E2]")
        return marked

    def _find_marker_positions(self, input_ids):
        e1_id = self.tokenizer.convert_tokens_to_ids("[E1]")
        e1e_id = self.tokenizer.convert_tokens_to_ids("[/E1]")
        e2_id = self.tokenizer.convert_tokens_to_ids("[E2]")
        e2e_id = self.tokenizer.convert_tokens_to_ids("[/E2]")

        pos = {"head_start": 0, "head_end": 0, "tail_start": 0, "tail_end": 0}
        for i, tid in enumerate(input_ids.tolist()):
            if tid == e1_id:
                pos["head_start"] = i
            elif tid == e1e_id:
                pos["head_end"] = i
            elif tid == e2_id:
                pos["tail_start"] = i
            elif tid == e2e_id:
                pos["tail_end"] = i
        return pos
