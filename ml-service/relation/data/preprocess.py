"""数据预处理主脚本：数据加载、增强、划分"""
import json
import os
import sys
import random
from typing import List, Dict, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from relation.data.config import TRAIN_CONFIG, RELATION_TYPES
from relation.data.duie_to_plmarker import convert_duie_file as duie_to_plm, convert_investment_data as inv_to_plm
from relation.data.duie_to_spn import convert_duie_file as duie_to_spn, convert_investment_data as inv_to_spn


def load_jsonl(path: str) -> List[Dict]:
    """加载JSONL格式数据"""
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def split_data(data: List[Dict], ratios: Tuple[float, ...] = (0.8, 0.1, 0.1)) -> Tuple[List, ...]:
    """按比例划分训练/验证/测试集"""
    random.seed(TRAIN_CONFIG["seed"])
    random.shuffle(data)
    n = len(data)
    train_end = int(n * ratios[0])
    val_end = train_end + int(n * ratios[1])
    return data[:train_end], data[train_end:val_end], data[val_end:]


def augment_investment_sample(sample: Dict) -> List[Dict]:
    """投融资领域数据增强：同义替换"""
    augmented = [sample]

    # 轮次同义替换
    round_synonyms = {
        "A轮": ["A轮融资", "A-round"],
        "B轮": ["B轮融资", "B-round"],
        "天使轮": ["种子轮", "种子轮融资"],
        "C轮": ["C轮融资", "C-round"],
    }

    for orig, syns in round_synonyms.items():
        if orig in sample.get("description", ""):
            for syn in syns:
                new_sample = dict(sample)
                new_sample["description"] = sample["description"].replace(orig, syn)
                new_sample["round"] = syn
                augmented.append(new_sample)

    return augmented


def prepare_training_data(investment_data_path: str, output_dir: str, duie_data_path: str = None):
    """准备完整训练数据集"""
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "pl_marker"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "spn"), exist_ok=True)

    # 1. 处理投融资数据
    print("=== 处理投融资数据 ===")
    inv_plm_path = os.path.join(output_dir, "pl_marker", "investment.jsonl")
    inv_spn_path = os.path.join(output_dir, "spn", "investment.jsonl")

    if os.path.exists(investment_data_path):
        inv_to_plm(investment_data_path, inv_plm_path)
        inv_to_spn(investment_data_path, inv_spn_path)

    # 2. 处理DuIE数据（如果提供）
    if duie_data_path and os.path.exists(duie_data_path):
        print("=== 处理DuIE2.0数据 ===")
        duie_plm_path = os.path.join(output_dir, "pl_marker", "duie.jsonl")
        duie_spn_path = os.path.join(output_dir, "spn", "duie.jsonl")
        duie_to_plm(duie_data_path, duie_plm_path)
        duie_to_spn(duie_data_path, duie_spn_path)

    # 3. 合并+增强+划分
    for fmt in ["pl_marker", "spn"]:
        all_data = []
        fmt_dir = os.path.join(output_dir, fmt)
        for f in os.listdir(fmt_dir):
            if f.endswith(".jsonl") and f not in ["train.jsonl", "val.jsonl", "test.jsonl"]:
                all_data.extend(load_jsonl(os.path.join(fmt_dir, f)))

        # 数据增强（仅对投融资数据）
        if fmt == "pl_marker":
            augmented = []
            for sample in all_data:
                augmented.extend(augment_investment_sample(sample))
            all_data = augmented

        print(f"\n{fmt}: 合并后共 {len(all_data)} 条")

        if len(all_data) < 10:
            print(f"  警告: 数据量不足({len(all_data)}条)，无法划分。请提供更多数据。")
            continue

        train, val, test = split_data(all_data)
        print(f"  划分: train={len(train)}, val={len(val)}, test={len(test)}")

        for name, subset in [("train", train), ("val", val), ("test", test)]:
            path = os.path.join(fmt_dir, f"{name}.jsonl")
            with open(path, 'w', encoding='utf-8') as f:
                for item in subset:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')

    print("\n=== 数据预处理完成 ===")


if __name__ == "__main__":
    inv_data = os.path.join(BASE_DIR, "..", "data", "processed", "investment_events_clean.json")
    out_dir = os.path.join(BASE_DIR, "data")

    # 如果DuIE数据存在则使用
    duie_path = os.path.join(BASE_DIR, "data", "duie", "duie_train.json")

    prepare_training_data(inv_data, out_dir, duie_path if os.path.exists(duie_path) else None)
