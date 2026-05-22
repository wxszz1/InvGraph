package com.srt.kg.entity;

public class Enterprise {
    private Long id;
    private String name;
    private String foundingDate;
    private Long industryId;
    private java.math.BigDecimal valuation;
    private String status;
    private String description;
    private java.sql.Timestamp createdAt;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getFoundingDate() { return foundingDate; }
    public void setFoundingDate(String foundingDate) { this.foundingDate = foundingDate; }

    public Long getIndustryId() { return industryId; }
    public void setIndustryId(Long industryId) { this.industryId = industryId; }

    public java.math.BigDecimal getValuation() { return valuation; }
    public void setValuation(java.math.BigDecimal valuation) { this.valuation = valuation; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }

    public java.sql.Timestamp getCreatedAt() { return createdAt; }
    public void setCreatedAt(java.sql.Timestamp createdAt) { this.createdAt = createdAt; }
}
