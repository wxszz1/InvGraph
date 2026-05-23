-- 融合时序特征的投融资风险知识图谱 — MySQL建表脚本
-- 三级模式：Industry → Enterprise → Investor

CREATE DATABASE IF NOT EXISTS srt_kg_invgraph DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE srt_kg_invgraph;

-- 行业分类表
CREATE TABLE IF NOT EXISTS industry (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE COMMENT '行业名称',
    policy_date VARCHAR(20) COMMENT '最近政策时间',
    hotness_score DECIMAL(5,2) DEFAULT 0 COMMENT '热度评分',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='行业分类';

-- 企业表
CREATE TABLE IF NOT EXISTS enterprise (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL COMMENT '企业名称',
    founding_date VARCHAR(20) COMMENT '成立日期',
    industry_id BIGINT COMMENT '所属行业ID',
    valuation DECIMAL(15,2) COMMENT '估值（万元）',
    status VARCHAR(20) DEFAULT 'active' COMMENT '经营状态: active/acquired/ipo/bankrupt',
    description TEXT COMMENT '企业简介',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_industry (industry_id),
    FOREIGN KEY (industry_id) REFERENCES industry(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='企业';

-- 投资机构表
CREATE TABLE IF NOT EXISTS investor (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL COMMENT '机构名称',
    type VARCHAR(20) COMMENT '类型: VC/PE/Angel/Government/Corporate',
    aum DECIMAL(15,2) COMMENT '管理规模（万元）',
    focus_industry VARCHAR(200) COMMENT '关注行业',
    description TEXT COMMENT '机构简介',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='投资机构';

-- 投资事件表
CREATE TABLE IF NOT EXISTS investment_event (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    investor_id BIGINT NOT NULL COMMENT '投资方ID',
    enterprise_id BIGINT NOT NULL COMMENT '企业ID',
    round VARCHAR(50) COMMENT '融资轮次: 天使轮/A轮/B轮/C轮/...',
    amount DECIMAL(15,2) COMMENT '投资金额（万元）',
    time VARCHAR(20) COMMENT '投资时间（年或年-月）',
    lead_flag TINYINT DEFAULT 0 COMMENT '是否领投: 1=领投 0=跟投',
    relation VARCHAR(20) DEFAULT 'INVEST' COMMENT '关系类型: INVEST/LEAD/FOLLOW/ACQUIRE',
    source TEXT COMMENT '数据来源',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_investor (investor_id),
    INDEX idx_enterprise (enterprise_id),
    INDEX idx_time (time),
    FOREIGN KEY (investor_id) REFERENCES investor(id),
    FOREIGN KEY (enterprise_id) REFERENCES enterprise(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='投资事件';
