"""DuIE2.0 JSON → PL-Marker训练格式（entity span标注 + relation label）

输入格式（DuIE2.0）:
{
  "text": "刘德华Andy出生于香港...",
  "spo_list": [
    {"subject": "刘德华", "predicate": "出生地", "object": "香港"}
  ]
}

输出格式（PL-Marker）:
{
  "tokens": ["刘", "德", "华", ...],
  "entities": [{"start": 0, "end": 3, "type": "PER"}],
  "relations": [{"head": 0, "tail": 1, "type": "出生地"}]
}
"""
import json
import os
import sys
from typing import List, Dict, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from relation.data.config import RELATION_TYPES, RELATION2ID, ENTITY_TYPES


def find_entity_span(tokens: List[str], entity_name: str) -> Optional[Dict]:
    """在token列表中查找实体的字符级span"""
    entity_chars = list(entity_name)
    for i in range(len(tokens) - len(entity_chars) + 1):
        if tokens[i:i+len(entity_chars)] == entity_chars:
            return {"start": i, "end": i + len(entity_chars)}
    return None


def convert_sample(sample: Dict) -> Optional[Dict]:
    """转换单条DuIE样本为PL-Marker格式"""
    text = sample["text"]
    tokens = list(text)  # 字符级分词
    spo_list = sample.get("spo_list", [])

    entities = []
    entity_map = {}  # (name, type) -> entity_idx
    relations = []

    for spo in spo_list:
        subj = spo["subject"]
        obj = spo["object"]
        # 对于DuIE2.0, object可能是字符串或dict
        if isinstance(obj, dict):
            obj_name = obj.get("@value", obj.get("value", ""))
        else:
            obj_name = str(obj)

        pred = spo["predicate"]

        # 查找subject span
        subj_span = find_entity_span(tokens, subj)
        if subj_span is None:
            continue

        # 查找object span
        obj_span = find_entity_span(tokens, obj_name)
        if obj_span is None:
            continue

        # 添加实体（去重）
        subj_key = (subj, "subject")
        obj_key = (obj_name, "object")

        if subj_key not in entity_map:
            entity_map[subj_key] = len(entities)
            entities.append({**subj_span, "type": "subject", "name": subj})

        if obj_key not in entity_map:
            entity_map[obj_key] = len(entities)
            entities.append({**obj_span, "type": "object", "name": obj_name})

        relations.append({
            "head": entity_map[subj_key],
            "tail": entity_map[obj_key],
            "type": pred,
        })

    if not entities:
        return None

    return {
        "tokens": tokens,
        "entities": entities,
        "relations": relations,
        "text": text,
    }


def convert_duie_file(input_path: str, output_path: str) -> int:
    """转换DuIE2.0文件为PL-Marker格式"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    count = 0

    with open(input_path, 'r', encoding='utf-8') as fin, \
         open(output_path, 'w', encoding='utf-8') as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            sample = json.loads(line)
            converted = convert_sample(sample)
            if converted:
                fout.write(json.dumps(converted, ensure_ascii=False) + '\n')
                count += 1

    print(f"PL-Marker格式转换完成: {count} 条有效样本 → {output_path}")
    return count


def convert_investment_data(input_path: str, output_path: str) -> int:
    """将我们的投融资数据转换为PL-Marker训练格式"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    count = 0
    with open(output_path, 'w', encoding='utf-8') as fout:
        for item in data:
            text = item.get("description", "")
            if not text:
                continue
            tokens = list(text)

            entities = []
            entity_map = {}
            relations = []

            # 企业实体
            ent_name = item.get("enterprise", "")
            if ent_name:
                span = find_entity_span(tokens, ent_name)
                if span:
                    key = (ent_name, "Enterprise")
                    entity_map[key] = len(entities)
                    entities.append({**span, "type": "Enterprise", "name": ent_name})

            # 投资方实体
            inv_name = item.get("investor", "")
            if inv_name:
                span = find_entity_span(tokens, inv_name)
                if span:
                    key = (inv_name, "Investor")
                    entity_map[key] = len(entities)
                    entities.append({**span, "type": "Investor", "name": inv_name})

            # 轮次实体
            round_name = item.get("round", "")
            if round_name:
                span = find_entity_span(tokens, round_name)
                if span:
                    key = (round_name, "Round")
                    entity_map[key] = len(entities)
                    entities.append({**span, "type": "Round", "name": round_name})

            # 行业实体
            ind_name = item.get("industry", "")
            if ind_name:
                span = find_entity_span(tokens, ind_name)
                if span:
                    key = (ind_name, "Industry")
                    entity_map[key] = len(entities)
                    entities.append({**span, "type": "Industry", "name": ind_name})

            # 生成关系
            if ent_name and inv_name:
                inv_key = (inv_name, "Investor")
                ent_key = (ent_name, "Enterprise")
                if inv_key in entity_map and ent_key in entity_map:
                    rel_type = "LEAD" if item.get("lead") else "INVEST"
                    relations.append({
                        "head": entity_map[inv_key],
                        "tail": entity_map[ent_key],
                        "type": rel_type,
                    })

            if entities and relations:
                fout.write(json.dumps({
                    "tokens": tokens,
                    "entities": entities,
                    "relations": relations,
                    "text": text,
                }, ensure_ascii=False) + '\n')
                count += 1

    print(f"投融资PL-Marker格式转换完成: {count} 条 → {output_path}")
    return count
