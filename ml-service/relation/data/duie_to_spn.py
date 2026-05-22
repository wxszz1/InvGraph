"""DuIE2.0 JSON → SPN训练格式（三元组集合）

SPN输出格式：
{
  "text": "...",
  "tokens": ["...", ...],
  "triple_set": [
    {"subject": "小米", "relation": "创始人", "object": "雷军"},
    ...
  ]
}
"""
import json
import os
import sys
from typing import List, Dict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from relation.data.config import RELATION_TYPES


def convert_sample_to_spn(sample: Dict) -> Dict:
    """转换单条DuIE样本为SPN格式"""
    text = sample["text"]
    tokens = list(text)
    spo_list = sample.get("spo_list", [])

    triple_set = []
    for spo in spo_list:
        obj = spo["object"]
        if isinstance(obj, dict):
            obj_name = obj.get("@value", obj.get("value", ""))
        else:
            obj_name = str(obj)

        triple_set.append({
            "subject": spo["subject"],
            "relation": spo["predicate"],
            "object": obj_name,
        })

    return {
        "text": text,
        "tokens": tokens,
        "triple_set": triple_set,
    }


def convert_duie_file(input_path: str, output_path: str) -> int:
    """转换DuIE2.0文件为SPN格式"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    count = 0

    with open(input_path, 'r', encoding='utf-8') as fin, \
         open(output_path, 'w', encoding='utf-8') as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            sample = json.loads(line)
            converted = convert_sample_to_spn(sample)
            if converted["triple_set"]:
                fout.write(json.dumps(converted, ensure_ascii=False) + '\n')
                count += 1

    print(f"SPN格式转换完成: {count} 条有效样本 → {output_path}")
    return count


def convert_investment_data(input_path: str, output_path: str) -> int:
    """将投融资数据转换为SPN训练格式"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    count = 0
    with open(output_path, 'w', encoding='utf-8') as fout:
        for item in data:
            text = item.get("description", "")
            if not text:
                continue

            triple_set = []
            ent = item.get("enterprise", "")
            inv = item.get("investor", "")

            if ent and inv:
                rel = "LEAD" if item.get("lead") else "INVEST"
                triple_set.append({
                    "subject": inv,
                    "relation": rel,
                    "object": ent,
                })

            if triple_set:
                fout.write(json.dumps({
                    "text": text,
                    "tokens": list(text),
                    "triple_set": triple_set,
                }, ensure_ascii=False) + '\n')
                count += 1

    print(f"投融资SPN格式转换完成: {count} 条 → {output_path}")
    return count
