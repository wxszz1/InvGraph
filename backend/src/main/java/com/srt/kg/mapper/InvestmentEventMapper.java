package com.srt.kg.mapper;

import com.srt.kg.entity.InvestmentEvent;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import java.util.List;
import java.util.Map;

@Mapper
public interface InvestmentEventMapper {
    List<InvestmentEvent> findByEnterpriseId(Long enterpriseId);
    List<Map<String, Object>> findByEnterpriseIdWithNames(Long enterpriseId);
    List<InvestmentEvent> findByInvestorId(Long investorId);
    List<InvestmentEvent> findAll(@Param("offset") int offset, @Param("limit") int limit);
    List<InvestmentEvent> findByTimeRange(@Param("startTime") String startTime, @Param("endTime") String endTime);
    List<Object> countByIndustryAndYear();  // returns {industry, year, count} maps
    int insert(InvestmentEvent event);
    int insertBatch(List<InvestmentEvent> list);
}
