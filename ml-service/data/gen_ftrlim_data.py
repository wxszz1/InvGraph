"""生成 FTRLIM 实体对齐训练数据"""
import json
import random
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

# 已知中英文别名映射（正样本）
ALIASES = [
    # 投资机构
    ({"name": "红杉资本", "type": "Investor"}, {"name": "Sequoia Capital", "type": "Investor"}),
    ({"name": "红杉中国", "type": "Investor"}, {"name": "Sequoia Capital China", "type": "Investor"}),
    ({"name": "高瓴资本", "type": "Investor"}, {"name": "Hillhouse Capital", "type": "Investor"}),
    ({"name": "IDG资本", "type": "Investor"}, {"name": "IDG Capital", "type": "Investor"}),
    ({"name": "金沙江创投", "type": "Investor"}, {"name": "GSR Ventures", "type": "Investor"}),
    ({"name": "启明创投", "type": "Investor"}, {"name": "Qiming Venture Partners", "type": "Investor"}),
    ({"name": "经纬创投", "type": "Investor"}, {"name": "Matrix Partners", "type": "Investor"}),
    ({"name": "经纬中国", "type": "Investor"}, {"name": "Matrix Partners China", "type": "Investor"}),
    ({"name": "真格基金", "type": "Investor"}, {"name": "ZhenFund", "type": "Investor"}),
    ({"name": "创新工场", "type": "Investor"}, {"name": "Sinovation Ventures", "type": "Investor"}),
    ({"name": "GGV纪源资本", "type": "Investor"}, {"name": "GGV Capital", "type": "Investor"}),
    ({"name": "晨兴资本", "type": "Investor"}, {"name": "Shunwei Capital", "type": "Investor"}),
    ({"name": "五源资本", "type": "Investor"}, {"name": "5Y Capital", "type": "Investor"}),
    ({"name": "联想创投", "type": "Investor"}, {"name": "Lenovo Capital", "type": "Investor"}),
    ({"name": "达晨财智", "type": "Investor"}, {"name": "Fortune Capital", "type": "Investor"}),
    ({"name": "深创投", "type": "Investor"}, {"name": "Shenzhen Capital Group", "type": "Investor"}),
    ({"name": "华平投资", "type": "Investor"}, {"name": "Warburg Pincus", "type": "Investor"}),
    ({"name": "凯雷投资", "type": "Investor"}, {"name": "The Carlyle Group", "type": "Investor"}),
    ({"name": "鼎晖投资", "type": "Investor"}, {"name": "CDH Investments", "type": "Investor"}),
    ({"name": "弘毅投资", "type": "Investor"}, {"name": "Legend Capital", "type": "Investor"}),
    ({"name": "春华资本", "type": "Investor"}, {"name": "Primavera Capital", "type": "Investor"}),
    ({"name": "高盛", "type": "Investor"}, {"name": "Goldman Sachs", "type": "Investor"}),
    ({"name": "摩根士丹利", "type": "Investor"}, {"name": "Morgan Stanley", "type": "Investor"}),
    ({"name": "中金公司", "type": "Investor"}, {"name": "CICC", "type": "Investor"}),
    ({"name": "中金资本", "type": "Investor"}, {"name": "CICC Capital", "type": "Investor"}),
    ({"name": "华兴资本", "type": "Investor"}, {"name": "China Renaissance", "type": "Investor"}),
    ({"name": "泰合资本", "type": "Investor"}, {"name": "Tahe Capital", "type": "Investor"}),
    ({"name": "软银愿景基金", "type": "Investor"}, {"name": "SoftBank Vision Fund", "type": "Investor"}),
    ({"name": "淡马锡", "type": "Investor"}, {"name": "Temasek", "type": "Investor"}),
    ({"name": "英特尔", "type": "Investor"}, {"name": "Intel Capital", "type": "Investor"}),
    # 企业
    ({"name": "字节跳动", "type": "Enterprise"}, {"name": "ByteDance", "type": "Enterprise"}),
    ({"name": "阿里巴巴", "type": "Enterprise"}, {"name": "Alibaba", "type": "Enterprise"}),
    ({"name": "腾讯", "type": "Enterprise"}, {"name": "Tencent", "type": "Enterprise"}),
    ({"name": "百度", "type": "Enterprise"}, {"name": "Baidu", "type": "Enterprise"}),
    ({"name": "京东", "type": "Enterprise"}, {"name": "JD.com", "type": "Enterprise"}),
    ({"name": "美团", "type": "Enterprise"}, {"name": "Meituan", "type": "Enterprise"}),
    ({"name": "拼多多", "type": "Enterprise"}, {"name": "Pinduoduo", "type": "Enterprise"}),
    ({"name": "网易", "type": "Enterprise"}, {"name": "NetEase", "type": "Enterprise"}),
    ({"name": "小米", "type": "Enterprise"}, {"name": "Xiaomi", "type": "Enterprise"}),
    ({"name": "滴滴", "type": "Enterprise"}, {"name": "DiDi", "type": "Enterprise"}),
    ({"name": "大疆", "type": "Enterprise"}, {"name": "DJI", "type": "Enterprise"}),
    ({"name": "商汤", "type": "Enterprise"}, {"name": "SenseTime", "type": "Enterprise"}),
    ({"name": "寒武纪", "type": "Enterprise"}, {"name": "Cambricon", "type": "Enterprise"}),
    ({"name": "蔚来", "type": "Enterprise"}, {"name": "NIO", "type": "Enterprise"}),
    ({"name": "小鹏", "type": "Enterprise"}, {"name": "XPeng", "type": "Enterprise"}),
    ({"name": "理想", "type": "Enterprise"}, {"name": "Li Auto", "type": "Enterprise"}),
    ({"name": "饿了么", "type": "Enterprise"}, {"name": "Ele.me", "type": "Enterprise"}),
    ({"name": "快手", "type": "Enterprise"}, {"name": "Kuaishou", "type": "Enterprise"}),
    ({"name": "小红书", "type": "Enterprise"}, {"name": "Xiaohongshu", "type": "Enterprise"}),
    ({"name": "哔哩哔哩", "type": "Enterprise"}, {"name": "Bilibili", "type": "Enterprise"}),
    # 简称/别名
    ({"name": "红杉资本", "type": "Investor"}, {"name": "红杉", "type": "Investor"}),
    ({"name": "高瓴资本", "type": "Investor"}, {"name": "高瓴", "type": "Investor"}),
    ({"name": "IDG资本", "type": "Investor"}, {"name": "IDG", "type": "Investor"}),
    ({"name": "字节跳动", "type": "Enterprise"}, {"name": "字节", "type": "Enterprise"}),
    ({"name": "阿里巴巴", "type": "Enterprise"}, {"name": "阿里", "type": "Enterprise"}),
    ({"name": "腾讯", "type": "Enterprise"}, {"name": "鹅厂", "type": "Enterprise"}),
    ({"name": "百度", "type": "Enterprise"}, {"name": "BIDU", "type": "Enterprise"}),
]

def gen_negative_pairs(enterprises, investors, n=200):
    """生成负样本对（不同类型或同类型但不同实体）"""
    pairs = []
    all_ents = [{"name": e, "type": "Enterprise"} for e in enterprises] + \
               [{"name": i, "type": "Investor"} for i in investors]

    # 同类型负样本
    ent_list = [{"name": e, "type": "Enterprise"} for e in enterprises]
    inv_list = [{"name": i, "type": "Investor"} for i in investors]

    random.seed(42)
    for _ in range(n // 2):
        a, b = random.sample(ent_list, 2)
        pairs.append((a, b))
    for _ in range(n // 2):
        a, b = random.sample(inv_list, 2)
        pairs.append((a, b))
    return pairs

def main():
    # 读取投资事件中的实体名
    with open('../../data/processed/investment_events_clean.json', 'r', encoding='utf-8') as f:
        events = json.load(f)

    enterprises = list(set(e['enterprise'] for e in events if e.get('enterprise')))
    investors = list(set(e['investor'] for e in events if e.get('investor')))

    # 正样本：别名对
    pos_pairs = []
    for a, b in ALIASES:
        pos_pairs.append((a, b))

    # 负样本：随机不同实体
    neg_pairs = gen_negative_pairs(enterprises, investors, n=200)

    # 合并
    all_pairs = pos_pairs + neg_pairs
    labels = [1] * len(pos_pairs) + [0] * len(neg_pairs)

    # 打乱
    combined = list(zip(all_pairs, labels))
    random.shuffle(combined)
    all_pairs, labels = zip(*combined)

    # 保存
    output = {
        "pairs": [{"a": a, "b": b} for a, b in all_pairs],
        "labels": list(labels),
    }
    os.makedirs('.', exist_ok=True)
    with open('ftrlim_training_data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(pos_pairs)} positive + {len(neg_pairs)} negative = {len(all_pairs)} total pairs")
    print(f"Saved to ftrlim_training_data.json")

if __name__ == '__main__':
    main()
