from pydantic import BaseModel
from typing import List, Optional


class Entity(BaseModel):
    name: str
    type: str  # Enterprise, Investor, Round, Industry
    is_time_sensitive: bool = False  # 是否为时间敏感属性


class Relation(BaseModel):
    head: str
    relation: str  # INVEST, ACQUIRE, LEAD, FOLLOW, BELONGS_TO, ...
    tail: str


class Triple(BaseModel):
    head: str
    relation: str
    tail: str
    time: Optional[str] = None
    head_type: Optional[str] = None  # 实体类型（用于导入Neo4j）
    tail_type: Optional[str] = None


class TimeExpression(BaseModel):
    text: str           # 原文
    normalized: str     # 规范化后
    start: int          # 在原文中的起始位置
    end: int            # 在原文中的结束位置


class MoneyExpression(BaseModel):
    text: str
    normalized: str
    start: int
    end: int


class NerRequest(BaseModel):
    text: str


class NerResponse(BaseModel):
    entities: List[Entity]
    times: List[TimeExpression] = []
    moneys: List[MoneyExpression] = []


class RelationRequest(BaseModel):
    text: str
    entities: List[Entity]


class RelationResponse(BaseModel):
    relations: List[Relation]


class ExtractRequest(BaseModel):
    text: str


class ExtractResponse(BaseModel):
    entities: List[Entity]
    relations: List[Relation]
    triples: List[Triple]
    times: List[TimeExpression] = []
    moneys: List[MoneyExpression] = []


class TrainRequest(BaseModel):
    model: str  # pl_marker / spn / ftrlim / mttr / preprocess
    epochs: int = 30
    batch_size: int = 16
    learning_rate: float = 2e-5


class ModelStatusResponse(BaseModel):
    status: str  # idle / training / done / error
    model: str = ""
    progress: float = 0.0  # 0-100
    message: str = ""
    metrics: dict = {}
