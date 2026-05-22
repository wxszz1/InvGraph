package com.srt.kg.entity;

public class Investor {
    private Long id;
    private String name;
    private String type;  // VC/PE/Angel/Government/Corporate
    private java.math.BigDecimal aum;
    private String focusIndustry;
    private String description;
    private java.sql.Timestamp createdAt;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getType() { return type; }
    public void setType(String type) { this.type = type; }

    public java.math.BigDecimal getAum() { return aum; }
    public void setAum(java.math.BigDecimal aum) { this.aum = aum; }

    public String getFocusIndustry() { return focusIndustry; }
    public void setFocusIndustry(String focusIndustry) { this.focusIndustry = focusIndustry; }

    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }

    public java.sql.Timestamp getCreatedAt() { return createdAt; }
    public void setCreatedAt(java.sql.Timestamp createdAt) { this.createdAt = createdAt; }
}
