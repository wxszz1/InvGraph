package com.srt.kg.entity;

public class InvestmentEvent {
    private Long id;
    private Long investorId;
    private Long enterpriseId;
    private String round;
    private java.math.BigDecimal amount;
    private String time;
    private Integer leadFlag;
    private String relation;
    private String source;
    private java.sql.Timestamp createdAt;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public Long getInvestorId() { return investorId; }
    public void setInvestorId(Long investorId) { this.investorId = investorId; }

    public Long getEnterpriseId() { return enterpriseId; }
    public void setEnterpriseId(Long enterpriseId) { this.enterpriseId = enterpriseId; }

    public String getRound() { return round; }
    public void setRound(String round) { this.round = round; }

    public java.math.BigDecimal getAmount() { return amount; }
    public void setAmount(java.math.BigDecimal amount) { this.amount = amount; }

    public String getTime() { return time; }
    public void setTime(String time) { this.time = time; }

    public Integer getLeadFlag() { return leadFlag; }
    public void setLeadFlag(Integer leadFlag) { this.leadFlag = leadFlag; }

    public String getRelation() { return relation; }
    public void setRelation(String relation) { this.relation = relation; }

    public String getSource() { return source; }
    public void setSource(String source) { this.source = source; }

    public java.sql.Timestamp getCreatedAt() { return createdAt; }
    public void setCreatedAt(java.sql.Timestamp createdAt) { this.createdAt = createdAt; }
}
