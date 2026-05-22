"""MultiObj分块算法

减少实体对齐的候选对数量：从O(n²)降到O(n·k)
- 按实体类型分块（只有同类型才比较）
- 按名称首字母分桶
- 按拼音首字母分桶
"""
from collections import defaultdict
from typing import List, Dict, Tuple


def _get_initial(name: str) -> str:
    """获取名称首字符（用于分桶）"""
    if not name:
        return "#"
    return name[0].upper()


def _get_pinyin_initial(name: str) -> str:
    """获取拼音首字母（简化：直接用首字符）"""
    # 简化实现，不依赖pypinyin
    return _get_initial(name)


class Blocker:
    """实体分块器"""

    def __init__(self, strategy: str = "type+initial"):
        self.strategy = strategy

    def block(self, entities: List[Dict]) -> List[List[Tuple[int, int]]]:
        """
        对实体列表进行分块，返回候选对组

        Args:
            entities: [{"name": ..., "type": ..., ...}, ...]
        Returns:
            每个block内的候选对索引列表 [(i, j), ...]
        """
        if self.strategy == "type+initial":
            return self._block_by_type_and_initial(entities)
        elif self.strategy == "type":
            return self._block_by_type(entities)
        else:
            return self._block_all(entities)

    def _block_by_type_and_initial(self, entities: List[Dict]) -> List[List[Tuple[int, int]]]:
        """按类型+首字母分块"""
        blocks = defaultdict(list)
        for i, e in enumerate(entities):
            etype = e.get("type", "unknown")
            initial = _get_initial(e.get("name", ""))
            key = f"{etype}:{initial}"
            blocks[key].append(i)

        result = []
        for key, indices in blocks.items():
            if len(indices) < 2:
                continue
            pairs = []
            for i in range(len(indices)):
                for j in range(i + 1, len(indices)):
                    pairs.append((indices[i], indices[j]))
            if pairs:
                result.append(pairs)

        return result

    def _block_by_type(self, entities: List[Dict]) -> List[List[Tuple[int, int]]]:
        """仅按类型分块"""
        blocks = defaultdict(list)
        for i, e in enumerate(entities):
            blocks[e.get("type", "unknown")].append(i)

        result = []
        for indices in blocks.values():
            if len(indices) < 2:
                continue
            pairs = []
            for i in range(len(indices)):
                for j in range(i + 1, len(indices)):
                    pairs.append((indices[i], indices[j]))
            if pairs:
                result.append(pairs)

        return result

    def _block_all(self, entities: List[Dict]) -> List[List[Tuple[int, int]]]:
        """不分块，返回所有候选对"""
        n = len(entities)
        pairs = []
        for i in range(n):
            for j in range(i + 1, n):
                pairs.append((i, j))
        return [pairs] if pairs else []
