"""时序约束验证器

验证投融资知识图谱中的时序一致性：
- 融资轮次递进性：天使轮时间 < A轮时间 < B轮时间
- 投资时间合理性：投资时间 >= 企业成立时间
- 同一轮次时间一致性：同一轮融资的不同投资方时间应接近
- 异常数据标记而非直接删除（保留审计记录）
"""
import re
from typing import List, Dict, Optional, Tuple
from temporal.normalizer import TimeNormalizer


# 轮次优先级（数字越大越靠后）
ROUND_PRIORITY = {
    "种子轮": 0, "天使轮": 1, "Pre-A轮": 2, "A轮": 3,
    "A+轮": 4, "Pre-B轮": 5, "B轮": 6, "B+轮": 7,
    "C轮": 8, "C+轮": 9, "D轮": 10, "E轮": 11,
    "F轮": 12, "Pre-IPO": 13, "IPO": 14,
}


class TemporalValidator:
    """时序约束验证器"""

    def __init__(self):
        self.normalizer = TimeNormalizer()
        self.anomalies: List[Dict] = []

    def _parse_time(self, time_str: Optional[str]) -> Optional[float]:
        """将时间字符串转为可比较的数值（年份.月份）"""
        if not time_str:
            return None
        normalized = self.normalizer.normalize(time_str)
        # 2023-06-15 → 2023.42...
        m = re.match(r'^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?', normalized)
        if not m:
            return None
        year = int(m.group(1))
        month = int(m.group(2)) if m.group(2) else 6
        return year + (month - 1) / 12.0

    def _get_round_priority(self, round_name: Optional[str]) -> Optional[int]:
        """获取轮次优先级"""
        if not round_name:
            return None
        # 尝试精确匹配
        if round_name in ROUND_PRIORITY:
            return ROUND_PRIORITY[round_name]
        # 模糊匹配（去掉"轮"后缀）
        clean = round_name.replace("轮", "")
        for key, val in ROUND_PRIORITY.items():
            if clean in key or key.startswith(clean):
                return val
        return None

    def validate_round_progression(self, events: List[Dict]) -> List[Dict]:
        """
        验证融资轮次递进性

        Args:
            events: [{"enterprise": "xx", "round": "A轮", "time": "2023", ...}, ...]
        Returns:
            anomalies: [{"type": "round_regression", "detail": "...", "events": [...]}]
        """
        anomalies = []
        # 按企业分组
        enterprise_events: Dict[str, List[Dict]] = {}
        for e in events:
            name = e.get("enterprise", e.get("head", ""))
            enterprise_events.setdefault(name, []).append(e)

        for ent_name, ent_events in enterprise_events.items():
            # 按时间排序
            sorted_events = sorted(
                ent_events,
                key=lambda x: self._parse_time(x.get("time", "")) or 0
            )
            # 检查轮次是否递进
            prev_round_val = -1
            for evt in sorted_events:
                round_val = self._get_round_priority(evt.get("round", ""))
                if round_val is not None and round_val < prev_round_val:
                    anomalies.append({
                        "type": "round_regression",
                        "enterprise": ent_name,
                        "detail": f"{ent_name}的{evt.get('round', '')}"
                                  f"发生在更早轮次之后",
                        "event": evt,
                    })
                if round_val is not None:
                    prev_round_val = max(prev_round_val, round_val)

        return anomalies

    def validate_investment_after_founding(
        self, events: List[Dict], enterprises: List[Dict]
    ) -> List[Dict]:
        """
        验证投资时间 >= 企业成立时间

        Args:
            events: 投资事件列表
            enterprises: [{"name": "xx", "founding_date": "2020", ...}, ...]
        Returns:
            anomalies
        """
        anomalies = []
        founding_map = {
            e["name"]: self._parse_time(e.get("founding_date", ""))
            for e in enterprises
            if e.get("founding_date")
        }

        for evt in events:
            ent_name = evt.get("enterprise", evt.get("tail", ""))
            invest_time = self._parse_time(evt.get("time", ""))
            founding_time = founding_map.get(ent_name)

            if invest_time and founding_time and invest_time < founding_time:
                anomalies.append({
                    "type": "invest_before_founding",
                    "enterprise": ent_name,
                    "detail": f"{ent_name}的投资时间"
                              f"({evt.get('time', '')})早于"
                              f"成立时间",
                    "event": evt,
                })

        return anomalies

    def validate_same_round_consistency(
        self, events: List[Dict]
    ) -> List[Dict]:
        """
        验证同一轮融资时间一致性

        同一轮次的不同投资方时间差不应超过1年
        """
        anomalies = []
        # 按(企业, 轮次)分组
        groups: Dict[Tuple[str, str], List[Dict]] = {}
        for evt in events:
            ent = evt.get("enterprise", evt.get("tail", ""))
            rnd = evt.get("round", "")
            if ent and rnd:
                groups.setdefault((ent, rnd), []).append(evt)

        for (ent, rnd), grp_events in groups.items():
            if len(grp_events) < 2:
                continue
            times = []
            for e in grp_events:
                t = self._parse_time(e.get("time", ""))
                if t is not None:
                    times.append(t)
            if len(times) >= 2 and max(times) - min(times) > 1.0:
                anomalies.append({
                    "type": "round_time_inconsistency",
                    "enterprise": ent,
                    "round": rnd,
                    "detail": f"{ent}的{rnd}不同投资方时间差超过1年",
                    "events": grp_events,
                })

        return anomalies

    def validate_all(
        self,
        events: List[Dict],
        enterprises: Optional[List[Dict]] = None
    ) -> Dict:
        """
        执行全部验证

        Returns:
            {
                "is_valid": bool,
                "anomaly_count": int,
                "anomalies": [...],
                "summary": str,
            }
        """
        all_anomalies = []

        # 1. 轮次递进性
        all_anomalies.extend(self.validate_round_progression(events))

        # 2. 投资时间合理性
        if enterprises:
            all_anomalies.extend(
                self.validate_investment_after_founding(events, enterprises)
            )

        # 3. 同一轮次时间一致性
        all_anomalies.extend(self.validate_same_round_consistency(events))

        self.anomalies = all_anomalies

        return {
            "is_valid": len(all_anomalies) == 0,
            "anomaly_count": len(all_anomalies),
            "anomalies": all_anomalies,
            "summary": (
                f"验证通过，共{len(events)}条事件无异常"
                if not all_anomalies
                else f"发现{len(all_anomalies)}条时序异常"
            ),
        }
