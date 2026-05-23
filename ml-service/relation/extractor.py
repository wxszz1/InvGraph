"""基于规则模板的关系抽取（改进版：分句+方向感知匹配）"""
import re
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from schemas import Entity, Relation
from ner.keywords import (
    INVEST_KEYWORDS, ACQUIRE_KEYWORDS, LEAD_KEYWORDS, FOLLOW_KEYWORDS
)

# 英文关系关键词
EN_INVEST_KEYWORDS = ["invested in", "invests in", "investment in", "funding for", "raised"]
EN_ACQUIRE_KEYWORDS = ["acquired", "acquires", "acquisition of", "purchased"]
EN_LEAD_KEYWORDS = ["led by", "led the", "leading the", "spearheaded"]
EN_FOLLOW_KEYWORDS = ["participated in", "participating", "joined in", "co-invested", "alongside", "joining"]

# 句子/分句分隔符
CLAUSE_SEPS = re.compile(r'[，。；、！？\n,;!?]')


class RelationExtractor:
    def __init__(self):
        self.relation_patterns = [
            (LEAD_KEYWORDS, "LEAD"),
            (FOLLOW_KEYWORDS, "FOLLOW"),
        ]

    def extract(self, text: str, entities: list) -> list[dict]:
        relations = []
        seen = set()

        def _get_type(e):
            return e["type"] if isinstance(e, dict) else e.type
        def _get_name(e):
            return e["name"] if isinstance(e, dict) else e.name

        investors = [e for e in entities if _get_type(e) == "Investor"]
        enterprises = [e for e in entities if _get_type(e) == "Enterprise"]

        clauses = self._split_clauses(text)

        # 1. LEAD/FOLLOW（投资者→企业）
        for keywords, rel_type in [(LEAD_KEYWORDS, "LEAD"), (FOLLOW_KEYWORDS, "FOLLOW")]:
            for kw in keywords:
                if kw not in text:
                    continue
                for clause, clause_start in clauses:
                    if kw not in clause:
                        continue
                    for kw_match in re.finditer(re.escape(kw), clause):
                        kw_pos = kw_match.start() + clause_start
                        best_inv = self._find_nearest_before(text, kw_pos, investors, _get_name)
                        best_ent = self._find_nearest_after(text, kw_pos, enterprises, _get_name)
                        # FOLLOW特殊处理：优先用已有LEAD关系的企业
                        if not best_ent and rel_type == "FOLLOW":
                            lead_ents = [r["tail"] for r in relations if r["relation"] == "LEAD"]
                            if lead_ents:
                                best_ent = lead_ents[-1]
                            else:
                                best_ent = self._find_nearest_before(text, kw_pos, enterprises, _get_name)
                        if not best_ent:
                            best_ent = self._find_nearest_global(text, kw_pos, enterprises, _get_name)
                        if best_inv and best_ent:
                            key = f"{best_inv}|{rel_type}|{best_ent}"
                            if key not in seen:
                                seen.add(key)
                                relations.append({"head": best_inv, "relation": rel_type, "tail": best_ent})

        # 1b. ACQUIRE（企业→企业：收购方在前，被收购方在后）
        for kw in ACQUIRE_KEYWORDS:
            if kw not in text:
                continue
            for clause, clause_start in clauses:
                if kw not in clause:
                    continue
                for kw_match in re.finditer(re.escape(kw), clause):
                    kw_pos = kw_match.start() + clause_start
                    acquirer = self._find_nearest_before(text, kw_pos, enterprises, _get_name)
                    target = self._find_nearest_after(text, kw_pos, enterprises, _get_name)
                    if not acquirer:
                        acquirer = self._find_nearest_global(text, kw_pos, enterprises, _get_name)
                    if not target:
                        target = self._find_nearest_global(text, kw_pos, enterprises, _get_name)
                    if acquirer and target and acquirer != target:
                        key = f"{acquirer}|ACQUIRE|{target}"
                        if key not in seen:
                            seen.add(key)
                            relations.append({"head": acquirer, "relation": "ACQUIRE", "tail": target})

        # 2. INVEST：分句内优先，再全局
        for kw in INVEST_KEYWORDS:
            if kw not in text:
                continue
            for clause, clause_start in clauses:
                if kw not in clause:
                    continue
                for kw_match in re.finditer(re.escape(kw), clause):
                    kw_pos = kw_match.start() + clause_start
                    # 模式A: 投资者在前，企业在后
                    inv_before = self._find_nearest_before(text, kw_pos, investors, _get_name)
                    ent_after = self._find_nearest_after(text, kw_pos, enterprises, _get_name)
                    # 如果同分句找不到，扩大范围
                    if not inv_before:
                        inv_before = self._find_nearest_global(text, kw_pos, investors, _get_name)
                    if not ent_after:
                        ent_after = self._find_nearest_global(text, kw_pos, enterprises, _get_name)
                    if inv_before and ent_after:
                        has_specific = any(
                            r["head"] == inv_before and r["tail"] == ent_after and r["relation"] != "INVEST"
                            for r in relations
                        )
                        if not has_specific:
                            key = f"{inv_before}|INVEST|{ent_after}"
                            if key not in seen:
                                seen.add(key)
                                relations.append({"head": inv_before, "relation": "INVEST", "tail": ent_after})

                    # 模式B: 企业在前，投资者在后
                    ent_before = self._find_nearest_before(text, kw_pos, enterprises, _get_name)
                    inv_after = self._find_nearest_after(text, kw_pos, investors, _get_name)
                    if not ent_before:
                        ent_before = self._find_nearest_global(text, kw_pos, enterprises, _get_name)
                    if not inv_after:
                        inv_after = self._find_nearest_global(text, kw_pos, investors, _get_name)
                    if ent_before and inv_after and (ent_before != ent_after if ent_after else True):
                        has_specific = any(
                            r["head"] == inv_after and r["tail"] == ent_before and r["relation"] != "INVEST"
                            for r in relations
                        )
                        if not has_specific:
                            key = f"{inv_after}|INVEST|{ent_before}"
                            if key not in seen:
                                seen.add(key)
                                relations.append({"head": inv_after, "relation": "INVEST", "tail": ent_before})

        # 3. English keywords（英文关系关键词匹配）
        text_lower = text.lower()
        for keywords, rel_type in [
            (EN_LEAD_KEYWORDS, "LEAD"),
            (EN_FOLLOW_KEYWORDS, "FOLLOW"),
            (EN_INVEST_KEYWORDS, "INVEST"),
            (EN_ACQUIRE_KEYWORDS, "ACQUIRE"),
        ]:
            for kw in keywords:
                if kw.lower() not in text_lower:
                    continue
                for clause, clause_start in clauses:
                    if kw.lower() not in clause.lower():
                        continue
                    for kw_match in re.finditer(re.escape(kw), clause, re.IGNORECASE):
                        kw_pos = kw_match.start() + clause_start
                        if rel_type == "ACQUIRE":
                            head = self._find_nearest_before(text, kw_pos, enterprises, _get_name)
                            tail = self._find_nearest_after(text, kw_pos, enterprises, _get_name)
                            if not head:
                                head = self._find_nearest_global(text, kw_pos, enterprises, _get_name)
                            if not tail:
                                tail = self._find_nearest_global(text, kw_pos, enterprises, _get_name)
                            if head and tail and head != tail:
                                key = f"{head}|{rel_type}|{tail}"
                                if key not in seen:
                                    seen.add(key)
                                    relations.append({"head": head, "relation": rel_type, "tail": tail})
                        elif rel_type in ("LEAD", "INVEST"):
                            head = self._find_nearest_before(text, kw_pos, investors, _get_name)
                            tail = self._find_nearest_after(text, kw_pos, enterprises, _get_name)
                            if not head:
                                head = self._find_nearest_global(text, kw_pos, investors, _get_name)
                            if not tail:
                                tail = self._find_nearest_global(text, kw_pos, enterprises, _get_name)
                            if head and tail and head != tail:
                                key = f"{head}|{rel_type}|{tail}"
                                if key not in seen:
                                    seen.add(key)
                                    relations.append({"head": head, "relation": rel_type, "tail": tail})
                        else:  # FOLLOW - find ALL investors before keyword (excluding LEAD investors)
                            lead_ents = [r["tail"] for r in relations if r["relation"] == "LEAD"]
                            lead_investors = set(r["head"] for r in relations if r["relation"] == "LEAD")
                            tail = lead_ents[-1] if lead_ents else self._find_nearest_global(text, kw_pos, enterprises, _get_name)
                            for inv in investors:
                                inv_name = _get_name(inv)
                                if inv_name in lead_investors:
                                    continue  # Skip investors already used for LEAD
                                if text.rfind(inv_name, 0, kw_pos) >= 0:
                                    if tail and inv_name != tail:
                                        key = f"{inv_name}|{rel_type}|{tail}"
                                        if key not in seen:
                                            seen.add(key)
                                            relations.append({"head": inv_name, "relation": rel_type, "tail": tail})

        return relations

    def _split_clauses(self, text):
        """将文本按标点分成子句"""
        clauses = []
        last_end = 0
        for m in CLAUSE_SEPS.finditer(text):
            clause = text[last_end:m.start()].strip()
            if clause:
                clauses.append((clause, last_end))
            last_end = m.end()
        clause = text[last_end:].strip()
        if clause:
            clauses.append((clause, last_end))
        if not clauses:
            clauses.append((text, 0))
        return clauses

    def _find_clause_boundaries(self, text, pos):
        """找到pos所在分句的起止位置"""
        clause_start = 0
        clause_end = len(text)
        for m in CLAUSE_SEPS.finditer(text):
            if m.end() <= pos:
                clause_start = m.end()
            elif m.start() > pos:
                clause_end = m.start()
                break
        return clause_start, clause_end

    def _find_nearest_before(self, text, pos, entities, get_name):
        """找到位置在pos之前最近的实体（优先同分句）"""
        clause_start, clause_end = self._find_clause_boundaries(text, pos)
        best = None
        best_dist = float('inf')
        for e in entities:
            name = get_name(e)
            # 先在同分句内找
            idx = text.rfind(name, clause_start, pos)
            if idx >= 0:
                dist = pos - idx
                if dist < best_dist:
                    best_dist = dist
                    best = name
        return best

    def _find_nearest_after(self, text, pos, entities, get_name):
        """找到位置在pos之后最近的实体（优先同分句）"""
        clause_start, clause_end = self._find_clause_boundaries(text, pos)
        best = None
        best_dist = float('inf')
        for e in entities:
            name = get_name(e)
            idx = text.find(name, pos, clause_end)
            if idx >= 0:
                dist = idx - pos
                if dist < best_dist:
                    best_dist = dist
                    best = name
        return best

    def _find_nearest_global(self, text, pos, entities, get_name):
        """全文找最近的实体（兜底）"""
        best = None
        best_dist = float('inf')
        for e in entities:
            name = get_name(e)
            idx = text.find(name)
            while idx >= 0:
                dist = abs(idx - pos)
                if dist < best_dist:
                    best_dist = dist
                    best = name
                idx = text.find(name, idx + 1)
        return best

    def _find_nearest(self, text, pos, entities, get_name):
        """找到距离给定位置最近的实体（向后兼容）"""
        return self._find_nearest_global(text, pos, entities, get_name)
