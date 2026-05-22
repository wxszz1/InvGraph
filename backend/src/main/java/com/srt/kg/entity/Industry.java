package com.srt.kg.entity;

public class Industry {
    private Long id;
    private String name;
    private String policyDate;
    private java.math.BigDecimal hotnessScore;
    private java.sql.Timestamp createdAt;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getPolicyDate() { return policyDate; }
    public void setPolicyDate(String policyDate) { this.policyDate = policyDate; }

    public java.math.BigDecimal getHotnessScore() { return hotnessScore; }
    public void setHotnessScore(java.math.BigDecimal hotnessScore) { this.hotnessScore = hotnessScore; }

    public java.sql.Timestamp getCreatedAt() { return createdAt; }
    public void setCreatedAt(java.sql.Timestamp createdAt) { this.createdAt = createdAt; }
}
