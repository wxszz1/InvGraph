"""扩充SPN和PL-Marker训练数据（模板组合）"""
import json
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from ner.keywords import KNOWN_ENTERPRISES, KNOWN_INVESTORS, ROUND_KEYWORDS

# ========== 模板库 ==========
TEMPLATES = {
    "LEAD": [
        "{investor}领投{enterprise}{round}",
        "{investor}领投{enterprise}的{round}融资",
        "由{investor}领投，{enterprise}完成{round}",
        "{enterprise}{round}由{investor}领投",
        "{investor}作为领投方参与{enterprise}{round}",
        "{investor}领投了{enterprise}的{round}融资",
        "{enterprise}获{investor}领投的{round}融资",
        "本轮融资由{investor}领投，{enterprise}",
    ],
    "FOLLOW": [
        "{investor}跟投{enterprise}{round}",
        "{investor}参与{enterprise}的{round}跟投",
        "{investor}作为跟投方参与{enterprise}{round}",
        "{investor}跟投了{enterprise}的{round}融资",
    ],
    "INVEST": [
        "{investor}投资{enterprise}",
        "{investor}投资了{enterprise}",
        "{investor}注资{enterprise}",
        "{investor}对{enterprise}进行投资",
        "{enterprise}获得{investor}投资",
        "{enterprise}获得{investor}的战略投资",
        "{enterprise}完成由{investor}投资的{round}",
        "{investor}战略投资{enterprise}",
    ],
    "ACQUIRE": [
        "{enterprise_a}收购{enterprise_b}",
        "{enterprise_a}并购{enterprise_b}",
        "{enterprise_a}以{money}收购{enterprise_b}",
        "{enterprise_a}收购了{enterprise_b}",
        "{enterprise_a}宣布收购{enterprise_b}",
    ],
}

# ========== 实体池 ==========
ENTERPRISES = sorted(KNOWN_ENTERPRISES, key=len, reverse=True)[:50]
INVESTORS = sorted(KNOWN_INVESTORS, key=len, reverse=True)[:40]
ROUNDS = [r for r in ROUND_KEYWORDS if r not in ("并购",)]
MONEYS = ["10亿美元", "5亿美元", "3亿美元", "1亿美元", "5000万美元", "30亿人民币", "10亿人民币", "5亿元"]

# 额外投融资句子（从真实新闻中提取的模式）
EXTRA_SENTENCES = [
    # LEAD
    ("红杉资本领投美团点评C轮融资", "LEAD", "红杉资本", "美团"),
    ("高瓴资本领投蔚来汽车D轮", "LEAD", "高瓴资本", "蔚来汽车"),
    ("IDG资本领投小鹏汽车B轮", "LEAD", "IDG资本", "小鹏汽车"),
    ("经纬创投领投理想汽车A轮", "LEAD", "经纬创投", "理想汽车"),
    ("真格基金领投蜜雪冰城天使轮", "LEAD", "真格基金", "蜜雪冰城"),
    ("启明创投领投知乎B轮", "LEAD", "启明创投", "知乎"),
    ("今日资本领投拼多多C轮", "LEAD", "今日资本", "拼多多"),
    ("高榕资本领投快手A轮", "LEAD", "高榕资本", "快手"),
    ("金沙江创投领投滴滴出行天使轮", "LEAD", "金沙江创投", "滴滴"),
    ("创新工场领投小红书Pre-A轮", "LEAD", "创新工场", "小红书"),
    ("GGV纪源资本领投B站B轮", "LEAD", "GGV纪源资本", "B站"),
    ("光速资本领投大疆创新C轮", "LEAD", "光速资本", "大疆创新"),
    ("源码资本领投元气森林A轮", "LEAD", "源码资本", "元气森林"),
    ("华创资本领投瑞幸咖啡B轮", "LEAD", "华创资本", "瑞幸咖啡"),
    ("蓝驰创投领投叮咚买菜Pre-A轮", "LEAD", "蓝驰创投", "叮咚买菜"),
    ("达晨财智领投药明康德A轮", "LEAD", "达晨财智", "药明康德"),
    ("深创投领投寒武纪B轮", "LEAD", "深创投", "寒武纪"),
    ("北极光创投领投地平线A轮", "LEAD", "北极光创投", "地平线"),
    ("联想创投领投商汤科技C轮", "LEAD", "联想创投", "商汤科技"),
    ("五源资本领投完美日记B轮", "LEAD", "五源资本", "完美日记"),
    ("腾讯投资领投美团D轮", "LEAD", "腾讯投资", "美团"),
    ("阿里创投领投饿了么E轮", "LEAD", "阿里创投", "饿了么"),
    ("顺为资本领投蔚来汽车B轮", "LEAD", "顺为资本", "蔚来汽车"),
    ("华兴资本领投泡泡玛特C轮", "LEAD", "华兴资本", "泡泡玛特"),
    ("泰合资本领投贝壳找房B轮", "LEAD", "泰合资本", "贝壳找房"),
    ("Accel Partners领投大疆创新A轮", "LEAD", "Accel Partners", "大疆创新"),
    ("红杉中国领投极氪汽车A轮", "LEAD", "红杉中国", "极氪汽车"),
    ("鼎晖投资领投用友网络B轮", "LEAD", "鼎晖投资", "用友网络"),
    ("弘毅投资领投金蝶国际C轮", "LEAD", "弘毅投资", "金蝶国际"),
    ("春华资本领投百济神州D轮", "LEAD", "春华资本", "百济神州"),
    # FOLLOW
    ("高瓴资本跟投美团C轮", "FOLLOW", "高瓴资本", "美团"),
    ("腾讯投资跟投拼多多B轮", "FOLLOW", "腾讯投资", "拼多多"),
    ("IDG资本跟投蔚来汽车A轮", "FOLLOW", "IDG资本", "蔚来汽车"),
    ("经纬创投跟投小鹏汽车C轮", "FOLLOW", "经纬创投", "小鹏汽车"),
    ("红杉资本跟投字节跳动D轮", "FOLLOW", "红杉资本", "字节跳动"),
    ("启明创投跟投知乎C轮", "FOLLOW", "启明创投", "知乎"),
    ("真格基金跟投蜜雪冰城A轮", "FOLLOW", "真格基金", "蜜雪冰城"),
    ("今日资本跟投快手B轮", "FOLLOW", "今日资本", "快手"),
    ("金沙江创投跟投滴滴出行B轮", "FOLLOW", "金沙江创投", "滴滴"),
    ("创新工场跟投小红书A轮", "FOLLOW", "创新工场", "小红书"),
    ("华平投资跟投菜鸟网络C轮", "FOLLOW", "华平投资", "菜鸟网络"),
    ("KKR跟投字节跳动E轮", "FOLLOW", "KKR", "字节跳动"),
    ("淡马锡跟投蚂蚁集团D轮", "FOLLOW", "淡马锡", "蚂蚁集团"),
    ("软银愿景基金跟投滴滴出行F轮", "FOLLOW", "软银愿景基金", "滴滴"),
    ("博裕资本跟投理想汽车C轮", "FOLLOW", "博裕资本", "理想汽车"),
    # INVEST
    ("腾讯投资美团", "INVEST", "腾讯投资", "美团"),
    ("阿里巴巴投资饿了么", "INVEST", "阿里巴巴", "饿了么"),
    ("红杉资本投资字节跳动", "INVEST", "红杉资本", "字节跳动"),
    ("高瓴资本战略投资蔚来汽车", "INVEST", "高瓴资本", "蔚来汽车"),
    ("IDG资本投资小鹏汽车", "INVEST", "IDG资本", "小鹏汽车"),
    ("百度投资携程", "INVEST", "百度", "携程"),
    ("京东投资永辉超市", "INVEST", "京东", "永辉超市"),
    ("小米战投投资紫米科技", "INVEST", "小米战投", "紫米科技"),
    ("拼多多获得腾讯投资", "INVEST", "腾讯投资", "拼多多"),
    ("快手获得百度投资", "INVEST", "百度", "快手"),
    ("蔚来汽车获得腾讯战略投资", "INVEST", "腾讯投资", "蔚来汽车"),
    ("小红书获得阿里创投投资", "INVEST", "阿里创投", "小红书"),
    ("蚂蚁集团投资用友网络", "INVEST", "蚂蚁集团", "用友网络"),
    ("深创投投资大疆创新", "INVEST", "深创投", "大疆创新"),
    ("中信产业基金投资顺丰", "INVEST", "中信产业基金", "顺丰"),
    ("华平投资投资中通快递", "INVEST", "华平投资", "中通快递"),
    ("凯雷投资投资陆金所", "INVEST", "凯雷投资", "陆金所"),
    ("中金公司投资微众银行", "INVEST", "中金公司", "微众银行"),
    ("晨兴资本投资小米", "INVEST", "晨兴资本", "小米"),
    ("云九资本投资知乎", "INVEST", "云九资本", "知乎"),
    ("嘉御资本投资喜茶", "INVEST", "嘉御资本", "喜茶"),
    ("元生资本投资叮咚买菜", "INVEST", "元生资本", "叮咚买菜"),
    ("钟鼎资本投资货拉拉", "INVEST", "钟鼎资本", "货拉拉"),
    ("渶策资本投资完美日记", "INVEST", "渶策资本", "完美日记"),
    ("北极光创投投资寒武纪", "INVEST", "北极光创投", "寒武纪"),
    # ACQUIRE
    ("阿里巴巴收购饿了么", "ACQUIRE", "阿里巴巴", "饿了么"),
    ("腾讯并购搜狗", "ACQUIRE", "腾讯", "搜狗"),
    ("百度收购爱奇艺", "ACQUIRE", "百度", "爱奇艺"),
    ("阿里巴巴并购优酷土豆", "ACQUIRE", "阿里巴巴", "优酷"),
    ("京东收购1号店", "ACQUIRE", "京东", "1号店"),
    ("美团收购摩拜单车", "ACQUIRE", "美团", "摩拜单车"),
    ("滴滴收购小蓝单车", "ACQUIRE", "滴滴", "小蓝单车"),
    ("字节跳动收购锤子科技", "ACQUIRE", "字节跳动", "锤子科技"),
    ("小米收购紫米科技", "ACQUIRE", "小米", "紫米科技"),
    ("腾讯收购Supercell", "ACQUIRE", "腾讯", "Supercell"),
]


def tokenize(text):
    """逐字符分词（与现有数据格式一致）"""
    return list(text)


def build_spn_sample(text, triples):
    """构建SPN格式样本"""
    return {
        "text": text,
        "tokens": tokenize(text),
        "triple_set": triples,
    }


def build_plm_sample(text, entities, relations):
    """构建PL-Marker格式样本"""
    tokens = tokenize(text)
    # 重新计算entity的start/end（基于逐字符token）
    plm_entities = []
    for ent in entities:
        name = ent["name"]
        idx = text.find(name)
        if idx >= 0:
            plm_entities.append({
                "start": idx,
                "end": idx + len(name),
                "type": ent["type"],
                "name": name,
            })
    return {
        "tokens": tokens,
        "entities": plm_entities,
        "relations": relations,
        "text": text,
    }


def generate_from_templates():
    """从模板组合生成数据"""
    samples = []

    # LEAD/FOLLOW/INVEST 模板
    for rel_type in ["LEAD", "FOLLOW", "INVEST"]:
        for tmpl in TEMPLATES[rel_type]:
            for inv in INVESTORS[:20]:
                for ent in ENTERPRISES[:20]:
                    for rnd in ROUNDS[:4]:
                        try:
                            text = tmpl.format(
                                investor=inv, enterprise=ent, round=rnd,
                                enterprise_a=ent, enterprise_b=inv, money=MONEYS[0]
                            )
                        except (KeyError, IndexError):
                            continue
                        samples.append((text, rel_type, inv, ent))

    # ACQUIRE 模板
    for tmpl in TEMPLATES["ACQUIRE"]:
        for ea in ENTERPRISES[:10]:
            for eb in ENTERPRISES[10:20]:
                if ea == eb:
                    continue
                for money in MONEYS[:2]:
                    try:
                        text = tmpl.format(
                            investor="", enterprise="", round="",
                            enterprise_a=ea, enterprise_b=eb, money=money,
                        )
                    except (KeyError, IndexError):
                        continue
                    samples.append((text, "ACQUIRE", ea, eb))

    return samples


def deduplicate(samples):
    """去重"""
    seen = set()
    result = []
    for s in samples:
        text = s[0]
        if text not in seen:
            seen.add(text)
            result.append(s)
    return result


def main():
    print("=== 生成模板组合数据 ===")
    template_samples = generate_from_templates()
    print(f"  模板生成: {len(template_samples)} 条")

    print("=== 合并额外句子 ===")
    all_samples = deduplicate(template_samples + EXTRA_SENTENCES)
    print(f"  去重后总计: {len(all_samples)} 条")

    # 构建SPN和PL-Marker格式
    spn_data = []
    plm_data = []

    for text, rel_type, head, tail in all_samples:
        # SPN格式
        spn_data.append(build_spn_sample(text, [
            {"subject": head, "relation": rel_type, "object": tail}
        ]))

        # PL-Marker格式
        entities = [
            {"name": head, "type": "Investor" if rel_type != "ACQUIRE" else "Enterprise"},
            {"name": tail, "type": "Enterprise"},
        ]
        # 加入round实体
        for rnd in ROUND_KEYWORDS:
            if rnd in text:
                entities.append({"name": rnd, "type": "Round"})
                break
        plm_data.append(build_plm_sample(text, entities, [
            {"head": 0, "tail": 1, "type": rel_type}
        ]))

    # 合并原有数据
    for path, data_list in [
        (os.path.join(BASE_DIR, "data/spn/investment.jsonl"), spn_data),
        (os.path.join(BASE_DIR, "data/pl_marker/investment.jsonl"), plm_data),
    ]:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        existing = json.loads(line)
                        # 用text去重
                        if not any(json.dumps(d, ensure_ascii=False) == json.dumps(existing, ensure_ascii=False)
                                   for d in data_list):
                            data_list.append(existing)

    # 打乱顺序并分割
    import random
    random.seed(42)

    for name, data in [("spn", spn_data), ("pl_marker", plm_data)]:
        random.shuffle(data)
        n = len(data)
        train_end = int(n * 0.8)
        val_end = int(n * 0.9)

        train, val, test = data[:train_end], data[train_end:val_end], data[val_end:]

        data_dir = os.path.join(BASE_DIR, f"data/{name}")
        for split_name, split_data in [("train", train), ("val", val), ("test", test), ("investment", data)]:
            path = os.path.join(data_dir, f"{split_name}.jsonl")
            with open(path, "w", encoding="utf-8") as f:
                for item in split_data:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
            print(f"  {name}/{split_name}.jsonl: {len(split_data)} 条")

    print("\n=== 数据扩充完成 ===")


if __name__ == "__main__":
    main()
