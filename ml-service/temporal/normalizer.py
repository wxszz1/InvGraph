"""时间规范化模块

将各种时间表达式规范化为统一格式：
- "2023年" → "2023"
- "2023年Q3" → "2023-Q3"
- "2023-06" → "2023-06"
- "去年" → 当前年-1
- "近期" → None
"""
import re
from datetime import datetime


class TimeNormalizer:
    """时间规范化器"""

    def __init__(self):
        self.current_year = datetime.now().year

        # 相对时间映射
        self.relative_map = {
            "去年": lambda: str(self.current_year - 1),
            "前年": lambda: str(self.current_year - 2),
            "今年": lambda: str(self.current_year),
            "明年": lambda: str(self.current_year + 1),
        }

        # 季度映射
        self.quarter_map = {
            "一季度": "Q1", "上半年": "H1", "二季度": "Q2",
            "三季度": "Q3", "下半年": "H2", "四季度": "Q4",
            "Q1": "Q1", "Q2": "Q2", "Q3": "Q3", "Q4": "Q4",
        }

    def normalize(self, time_text: str) -> str:
        """规范化时间表达式"""
        if not time_text:
            return ""

        text = time_text.strip()

        # 相对时间
        for rel, func in self.relative_map.items():
            if rel in text:
                return func()

        # 完整日期: 2023-06-15 or 2023/06/15
        m = re.match(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', text)
        if m:
            return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"

        # 年月: 2023-06 or 2023年6月
        m = re.match(r'(\d{4})[-/年](\d{1,2})', text)
        if m:
            return f"{m.group(1)}-{int(m.group(2)):02d}"

        # 年+季度: 2023年Q3 or 2023-Q3
        m = re.match(r'(\d{4})[-年]?(Q\d)', text)
        if m:
            return f"{m.group(1)}-{m.group(2)}"

        # 纯年: 2023年 or 2023
        m = re.match(r'(\d{4})年?$', text)
        if m:
            return m.group(1)

        # 中文季度
        for cn, en in self.quarter_map.items():
            if cn in text:
                year_m = re.search(r'(\d{4})', text)
                if year_m:
                    return f"{year_m.group(1)}-{en}"

        return text

    def extract_and_normalize(self, text: str) -> list:
        """从文本中提取并规范化所有时间表达式"""
        patterns = [
            (r'(\d{4}年\d{1,2}月\d{1,2}日)', None),
            (r'(\d{4}年\d{1,2}月)', None),
            (r'(\d{4}年[一二三四]季度)', None),
            (r'(\d{4}年Q[1-4])', None),
            (r'(\d{4}年)', None),
            (r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', None),
            (r'(\d{4}[-/]\d{1,2})', None),
            (r'(去年|前年|今年)', None),
        ]

        results = []
        seen = set()
        for pattern, _ in patterns:
            for m in re.finditer(pattern, text):
                raw = m.group(1)
                if raw not in seen:
                    seen.add(raw)
                    normalized = self.normalize(raw)
                    results.append({
                        "text": raw,
                        "normalized": normalized,
                        "start": m.start(1),
                        "end": m.end(1),
                    })

        return sorted(results, key=lambda x: x["start"])
