"""基于HanLP 2.x + 关键词的投融资领域实体识别"""
import re
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ner.keywords import (
    ROUND_KEYWORDS, INDUSTRY_KEYWORDS, INVESTOR_SUFFIXES,
    KNOWN_ENTERPRISES, KNOWN_INVESTORS, ENTERPRISE_SUFFIXES,
    INVEST_KEYWORDS, ACQUIRE_KEYWORDS, LEAD_KEYWORDS, FOLLOW_KEYWORDS,
)
from schema.ontology import ROUND_KEYWORDS as ONTOLOGY_ROUNDS
from schemas import Entity

# 连接词/分隔符，用于拆分复合实体
SPLITTERS = ['和', '、', '及', '以及', '与']


class NerRecognizer:
    def __init__(self):
        self.hanlp_ner = None
        self.hanlp_tok = None
        self._load_hanlp()

    def _load_hanlp(self):
        """加载HanLP 2.x模型（使用ELECTRA，无需TensorFlow）"""
        try:
            import hanlp
            self.hanlp_ner = hanlp.load(hanlp.pretrained.ner.MSRA_NER_ELECTRA_SMALL_ZH)
            self.hanlp_tok = hanlp.load(hanlp.pretrained.tok.FINE_ELECTRA_SMALL_ZH)
            print("[NerRecognizer] HanLP 2.x models loaded (ELECTRA)")
        except Exception as e:
            print(f"[NerRecognizer] HanLP load failed ({e}), using keyword-only mode")

    def recognize(self, text: str) -> list[dict]:
        """识别文本中的所有实体"""
        entities = []
        seen = set()

        # 1. HanLP NER
        hanlp_entities = self._hanlp_ner(text)
        for ent in hanlp_entities:
            key = (ent["name"], ent["type"])
            if key not in seen:
                seen.add(key)
                entities.append(ent)

        # 2. 已知企业（优先匹配，避免被后缀误匹配）
        for name in sorted(KNOWN_ENTERPRISES, key=len, reverse=True):
            if name in text and ("enterprise", name) not in seen:
                seen.add(("enterprise", name))
                entities.append({"name": name, "type": "Enterprise"})

        # 3. 已知投资机构（长名称优先）
        for name in sorted(KNOWN_INVESTORS, key=len, reverse=True):
            if name in text and ("investor", name) not in seen:
                seen.add(("investor", name))
                entities.append({"name": name, "type": "Investor"})

        # 4. 融资轮次
        for kw in ROUND_KEYWORDS:
            if kw in text and ("round", kw) not in seen:
                seen.add(("round", kw))
                entities.append({"name": kw, "type": "Round"})

        # 5. 行业分类
        for kw in INDUSTRY_KEYWORDS:
            if kw in text and ("industry", kw) not in seen:
                seen.add(("industry", kw))
                entities.append({"name": kw, "type": "Industry"})

        # 6. 企业名称后缀匹配（只匹配未被识别的部分）
        # 中文企业名
        suffix_pattern = '|'.join(re.escape(s) for s in ENTERPRISE_SUFFIXES)
        for match in re.finditer(rf'[一-鿿]{{2,8}}(?:{suffix_pattern})', text):
            name = match.group()
            if not any(name in e["name"] or e["name"] in name for e in entities):
                if ("enterprise", name) not in seen:
                    seen.add(("enterprise", name))
                    entities.append({"name": name, "type": "Enterprise"})

        # 6b. （移至步骤7b后处理，避免与投资者名冲突）

        # 7. 投资机构后缀匹配（拆分"腾讯和高瓴资本"等复合名称）
        # 常见前缀功能词（不应出现在实体名开头）
        FUNC_PREFIXES = ('由', '被', '将', '让', '给', '为', '对', '从', '向', '到', '在')
        # 关系关键词（不应出现在实体名中）
        REL_KEYWORDS = set(INVEST_KEYWORDS + ACQUIRE_KEYWORDS + LEAD_KEYWORDS + FOLLOW_KEYWORDS)
        # 时间前缀模式（不应出现在实体名开头）
        TIME_PREFIX_RE = re.compile(r'^\d{4}年\d{1,2}月?')

        inv_pattern = '|'.join(re.escape(s) for s in INVESTOR_SUFFIXES)
        for match in re.finditer(rf'[一-鿿A-Za-z0-9]{{2,10}}(?:{inv_pattern})', text):
            raw_name = match.group()
            # 跳过以时间开头的（如"2023年3月高瓴资本"）
            time_match = TIME_PREFIX_RE.match(raw_name)
            if time_match:
                raw_name = raw_name[time_match.end():]
                if len(raw_name) < 2:
                    continue
            # 跳过以功能词开头的（如"由红杉资本"）
            if raw_name[0] in FUNC_PREFIXES:
                # 尝试去掉前缀后重新检查
                stripped = raw_name[1:]
                for s in INVESTOR_SUFFIXES:
                    if stripped.endswith(s) and len(stripped) >= 2:
                        raw_name = stripped
                        break
                else:
                    continue
            # 跳过包含关系关键词的（如"美团获得腾讯战略投资"）
            if any(kw in raw_name for kw in REL_KEYWORDS if kw != raw_name):
                continue
            # 跳过：去掉投资者后缀后是已知企业的
            base_name = raw_name
            for s in sorted(INVESTOR_SUFFIXES, key=len, reverse=True):
                if base_name.endswith(s):
                    base_name = base_name[:-len(s)]
                    break
            if base_name in KNOWN_ENTERPRISES:
                continue
            # 如果包含连接词，拆分后逐个加入（跳过整个复合名称）
            if any(s in raw_name for s in SPLITTERS):
                parts = self._split_compound_name(raw_name, INVESTOR_SUFFIXES)
                for part_name in parts:
                    # 再次检查拆分后的部分
                    pbase = part_name
                    for s in sorted(INVESTOR_SUFFIXES, key=len, reverse=True):
                        if pbase.endswith(s):
                            pbase = pbase[:-len(s)]
                            break
                    if pbase in KNOWN_ENTERPRISES:
                        continue
                    if ("investor", part_name) not in seen:
                        seen.add(("investor", part_name))
                        if not any(e["name"] == part_name for e in entities):
                            entities.append({"name": part_name, "type": "Investor"})
                continue
            if ("investor", raw_name) not in seen:
                seen.add(("investor", raw_name))
                if not any(e["name"] == raw_name for e in entities):
                    entities.append({"name": raw_name, "type": "Investor"})

        # 7b. 英文投资机构名匹配（如 "Parkway Venture Capital", "AMD Ventures"）
        eng_inv_pattern = '|'.join(re.escape(s) for s in INVESTOR_SUFFIXES if s[0].isascii())
        if eng_inv_pattern:
            for match in re.finditer(rf'([A-Z][a-zA-Z0-9]+(?: [A-Z][a-zA-Z0-9]+)*)\s*(?:{eng_inv_pattern})', text):
                name = match.group().strip()
                # 去掉尾部标点
                name = re.sub(r'[，。、,;\s（(]+$', '', name)
                if len(name) >= 3 and ("investor_en", name) not in seen:
                    seen.add(("investor_en", name))
                    if not any(e["name"] == name for e in entities):
                        entities.append({"name": name, "type": "Investor"})

        # 6b. 英文企业名模式：独立大写英文单词（如 Hark, Figure）
        # 排除词集合：已识别实体名称中的所有单词
        excluded_words = set()
        for e in entities:
            for w in e["name"].split():
                excluded_words.add(w)
        # 常见非企业英文词
        COMMON_WORDS = {
            'The', 'This', 'That', 'From', 'With', 'For', 'And', 'But',
            'Not', 'Are', 'Was', 'Were', 'Been', 'Have', 'Has', 'Had',
            'Will', 'Would', 'Could', 'Should', 'May', 'Might', 'Can',
            'Their', 'There', 'These', 'Those', 'Here', 'Where', 'When',
            'What', 'Which', 'Who', 'How', 'All', 'Each', 'Every',
            'Both', 'Few', 'More', 'Most', 'Other', 'Some', 'Such',
            'Its', 'His', 'Her', 'Our', 'Your', 'My', 'Their',
            # 金融新闻常见词
            'Founder', 'CEO', 'CTO', 'President', 'Director',
            'Series', 'Round', 'Funding', 'Valued', 'Billion', 'Million',
            'Raising', 'Raised', 'Announced', 'Completed',
            'GPU', 'CPU', 'API', 'SDK', 'IoT',
            # 人名（常见英文名）
            'Brett', 'Adcock', 'Sam', 'Altman', 'Elon', 'Musk',
            'Tim', 'Cook', 'Satya', 'Nadella', 'Sundar', 'Pichai',
            'Mark', 'Zuckerberg', 'Jeff', 'Bezos', 'Andy', 'Jassy',
            'Jensen', 'Huang', 'Lisa', 'Su', 'Pat', 'Gelsinger',
            # 金额/轮次词
            'USD', 'Dollar', 'Dollars', 'Yuan', 'Euro',
            'Pre', 'Post', 'Seed', 'Angel', 'Series',
            # 其他常见词
            'Inc', 'Corp', 'Ltd', 'LLC', 'Co',
            'New', 'Old', 'Big', 'Small', 'Top', 'First', 'Second',
            'Led', 'By', 'In', 'On', 'At', 'To', 'Of',
        }
        for match in re.finditer(r'\b([A-Z][a-zA-Z]{1,15})\b', text):
            name = match.group()
            if name in COMMON_WORDS or name in excluded_words:
                continue
            if ("enterprise_en", name) not in seen and not any(e["name"] == name for e in entities):
                seen.add(("enterprise_en", name))
                entities.append({"name": name, "type": "Enterprise"})

        # 8. 清理：移除含连接词的复合实体（其组成部分已单独存在）
        entities = [
            e for e in entities
            if not (e["type"] == "Investor" and any(s in e["name"] for s in SPLITTERS))
        ]

        # 9. 清理：移除被投资机构名称包含的企业名（如"Intel"被"Intel Capital"包含）
        investor_names = [e["name"] for e in entities if e["type"] == "Investor"]
        entities = [
            e for e in entities
            if not (e["type"] == "Enterprise"
                    and any(e["name"] in inv and e["name"] != inv for inv in investor_names))
        ]

        return entities

    def _split_compound_name(self, raw: str, suffixes: list) -> list:
        """拆分复合投资机构名称，如'腾讯和高瓴资本' → ['腾讯', '高瓴资本']"""
        for splitter in SPLITTERS:
            if splitter in raw:
                parts = raw.split(splitter)
                results = []
                # 重建各部分：给没有后缀的前面部分加上后面部分的后缀
                for i, part in enumerate(parts):
                    part = part.strip()
                    if not part:
                        continue
                    # 如果最后一部分有后缀，前面部分缺后缀则补上
                    if i < len(parts) - 1 and not any(part.endswith(s) for s in suffixes):
                        # 找到后面最近的有后缀的部分的后缀
                        for j in range(i + 1, len(parts)):
                            for s in suffixes:
                                if parts[j].strip().endswith(s):
                                    part = part + s
                                    break
                            if any(part.endswith(s) for s in suffixes):
                                break
                    if len(part) >= 2:
                        results.append(part)
                return results
        return [raw]

    def _hanlp_ner(self, text: str) -> list[dict]:
        """使用HanLP进行NER"""
        if self.hanlp_ner is None:
            return []
        try:
            result = self.hanlp_ner(text)
            entities = []
            for item in result:
                if len(item) >= 2:
                    name, label = item[0], item[1]
                    entity_type = self._map_hanlp_label(label, name)
                    if entity_type:
                        entities.append({"name": name, "type": entity_type})
            return entities
        except Exception:
            return []

    def _map_hanlp_label(self, label: str, name: str) -> str | None:
        """将HanLP的NER标签映射为本体实体类型"""
        label_map = {
            "NR": None,   # 人名 → 暂不处理
            "NS": None,   # 地名 → 暂不处理
            "NT": "Enterprise",  # 机构名 → 默认为Enterprise
        }
        mapped = label_map.get(label)
        if mapped == "Enterprise":
            # 检查是否是已知投资机构
            if name in KNOWN_INVESTORS or any(name.endswith(s) for s in INVESTOR_SUFFIXES):
                return "Investor"
        return mapped

    def extract_time(self, text: str) -> list[dict]:
        """提取文本中的时间表达式"""
        from datetime import datetime
        times = []
        current_year = datetime.now().year

        # 相对时间
        relative_map = {
            "去年": str(current_year - 1),
            "前年": str(current_year - 2),
            "今年": str(current_year),
            "近期": str(current_year),
            "近日": str(current_year),
            "最近": str(current_year),
            "日前": str(current_year),
        }
        for rel, val in relative_map.items():
            for m in re.finditer(rel, text):
                times.append({
                    "text": m.group(), "normalized": val,
                    "start": m.start(), "end": m.end(),
                })

        patterns = [
            (r'(\d{4})年(\d{1,2})月(\d{1,2})日', lambda m: f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"),
            (r'(\d{4})年(\d{1,2})月', lambda m: f"{m.group(1)}-{int(m.group(2)):02d}"),
            (r'(\d{4})年', lambda m: m.group(1)),
            (r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', lambda m: f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"),
            (r'(\d{4})[-/](\d{1,2})', lambda m: f"{m.group(1)}-{int(m.group(2)):02d}"),
        ]
        for pattern, formatter in patterns:
            for match in re.finditer(pattern, text):
                times.append({
                    "text": match.group(),
                    "normalized": formatter(match),
                    "start": match.start(),
                    "end": match.end(),
                })
        return times

    def extract_money(self, text: str) -> list[dict]:
        """提取文本中的金额表达式"""
        amounts = []
        patterns = [
            (r'(\d+(?:\.\d+)?)\s*亿美元', lambda m: f"{float(m.group(1)) * 10000}万美元"),
            (r'(\d+(?:\.\d+)?)\s*亿元?(?:人民币)?', lambda m: f"{m.group(1)}亿元"),
            (r'(\d+(?:\.\d+)?)\s*万美元', lambda m: f"{m.group(1)}万美元"),
            (r'(\d+(?:\.\d+)?)\s*万(?:美元|人民币)', lambda m: f"{m.group(1)}万元"),
        ]
        for pattern, formatter in patterns:
            for match in re.finditer(pattern, text):
                amounts.append({
                    "text": match.group(),
                    "normalized": formatter(match),
                    "start": match.start(),
                    "end": match.end(),
                })
        # 去重：移除被更长匹配包含的短匹配
        amounts.sort(key=lambda x: (x["start"], -(x["end"] - x["start"])))
        filtered = []
        for a in amounts:
            if not any(a["start"] >= f["start"] and a["end"] <= f["end"] and a != f for f in filtered):
                filtered.append(a)
        return filtered

    def get_time_sensitive_entities(self, text: str) -> dict:
        """区分时间敏感和非敏感属性"""
        entities = self.recognize(text)
        result = {"time_sensitive": [], "time_constant": []}
        for ent in entities:
            if ent["type"] in ("Round",):
                result["time_sensitive"].append(ent)
            elif ent["type"] in ("Industry",):
                result["time_constant"].append(ent)
            else:
                # Enterprise/Investor的name是constant，但估值/金额是sensitive
                result["time_constant"].append(ent)
        return result
