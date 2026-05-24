"""生成 MTTR 神经时序推理模型的训练数据

从投资事件生成四元组，用规则版 TemporalReasoner 标注时序关系对。
"""
import json
import os
import sys
import random
from itertools import combinations

sys.stdout.reconfigure(encoding='utf-8')

RELATION_LIST = ["INVEST", "LEAD", "FOLLOW", "ACQUIRE", "BELONGS_TO", "COMPETE", "CO_INVEST"]
RELATION_MAP = {r: i for i, r in enumerate(RELATION_LIST)}
TEMPORAL_LIST = ["before", "after", "overlap", "simultaneous"]
TEMPORAL_MAP = {t: i for i, t in enumerate(TEMPORAL_LIST)}

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "mttr")
EVENTS_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "processed", "investment_events_clean.json")


def serialize_quadruple(q):
    """将四元组序列化为文本，用于BERT输入"""
    parts = [q["head"], q["relation"]]
    if q.get("tail"):
        parts.append(q["tail"])
    if q.get("time"):
        parts.append(q["time"])
    return " ".join(parts)


def gen_relation_samples(events):
    """生成关系分类训练样本"""
    samples = []
    seen = set()
    for ev in events:
        investor = ev.get("investor", "")
        enterprise = ev.get("enterprise", "")
        round_name = ev.get("round", "")
        time = ev.get("time", "")
        lead = ev.get("lead", False)

        if not investor or not enterprise:
            continue

        # 确定关系类型
        if lead:
            relation = "LEAD"
        else:
            relation = "INVEST"

        q = {"head": investor, "relation": relation, "tail": enterprise, "time": time}
        text = serialize_quadruple(q)
        if text in seen:
            continue
        seen.add(text)
        samples.append({
            "text": text,
            "relation_label": RELATION_MAP[relation],
        })

        # 添加 FOLLOW 变体
        q_follow = {"head": investor, "relation": "FOLLOW", "tail": enterprise, "time": time}
        text_follow = serialize_quadruple(q_follow)
        if text_follow not in seen:
            seen.add(text_follow)
            samples.append({
                "text": text_follow,
                "relation_label": RELATION_MAP["FOLLOW"],
            })

    return samples


def gen_temporal_samples(events):
    """生成时序关系对训练样本"""
    # 按企业分组
    by_enterprise = {}
    for ev in events:
        ent = ev.get("enterprise", "")
        if not ent:
            continue
        by_enterprise.setdefault(ent, []).append(ev)

    samples = []
    seen = set()

    for ent, evs in by_enterprise.items():
        if len(evs) < 2:
            continue
        for i, j in combinations(range(len(evs)), 2):
            ev_a, ev_b = evs[i], evs[j]
            time_a = ev_a.get("time", "")
            time_b = ev_b.get("time", "")
            round_a = ev_a.get("round", "")
            round_b = ev_b.get("round", "")

            # 构建四元组
            q_a = {"head": ev_a.get("investor", ""), "relation": "LEAD" if ev_a.get("lead") else "INVEST",
                   "tail": ent, "time": time_a}
            q_b = {"head": ev_b.get("investor", ""), "relation": "LEAD" if ev_b.get("lead") else "INVEST",
                   "tail": ent, "time": time_b}

            text_a = serialize_quadruple(q_a)
            text_b = serialize_quadruple(q_b)

            # 判断时序关系
            if time_a and time_b:
                if time_a < time_b:
                    temporal = "before"
                elif time_a > time_b:
                    temporal = "after"
                else:
                    temporal = "simultaneous"
            elif round_a and round_b:
                from schema.ontology import ROUND_KEYWORDS
                idx_a = ROUND_KEYWORDS.get(round_a, -1)
                idx_b = ROUND_KEYWORDS.get(round_b, -1)
                if idx_a < idx_b:
                    temporal = "before"
                elif idx_a > idx_b:
                    temporal = "after"
                else:
                    temporal = "simultaneous"
            else:
                temporal = "simultaneous"

            # 正样本：(A, B, temporal)
            key = tuple(sorted([text_a, text_b]))
            if key in seen:
                continue
            seen.add(key)

            samples.append({
                "text_a": text_a,
                "text_b": text_b,
                "temporal_label": TEMPORAL_MAP[temporal],
            })

            # 也加反向对
            reverse_map = {"before": "after", "after": "before", "simultaneous": "simultaneous", "overlap": "overlap"}
            samples.append({
                "text_a": text_b,
                "text_b": text_a,
                "temporal_label": TEMPORAL_MAP[reverse_map[temporal]],
            })

    return samples


def main():
    # 加载事件数据
    with open(EVENTS_PATH, 'r', encoding='utf-8') as f:
        events = json.load(f)

    print(f"Loaded {len(events)} investment events")

    # 生成关系分类数据
    rel_samples = gen_relation_samples(events)
    print(f"Generated {len(rel_samples)} relation classification samples")

    # 生成时序关系对数据
    temp_samples = gen_temporal_samples(events)
    print(f"Generated {len(temp_samples)} temporal relation pair samples")

    # 划分 train/val/test (80/10/10)
    random.seed(42)
    random.shuffle(rel_samples)
    random.shuffle(temp_samples)

    def split(data, ratios=(0.8, 0.1, 0.1)):
        n = len(data)
        t1 = int(n * ratios[0])
        t2 = int(n * (ratios[0] + ratios[1]))
        return data[:t1], data[t1:t2], data[t2:]

    rel_train, rel_val, rel_test = split(rel_samples)
    temp_train, temp_val, temp_test = split(temp_samples)

    # 保存
    os.makedirs(DATA_DIR, exist_ok=True)
    for name, data in [
        ("rel_train.jsonl", rel_train),
        ("rel_val.jsonl", rel_val),
        ("rel_test.jsonl", rel_test),
        ("temp_train.jsonl", temp_train),
        ("temp_val.jsonl", temp_val),
        ("temp_test.jsonl", temp_test),
    ]:
        path = os.path.join(DATA_DIR, name)
        with open(path, 'w', encoding='utf-8') as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"  {name}: {len(data)} samples")

    print(f"\nAll data saved to {DATA_DIR}")


if __name__ == "__main__":
    main()
