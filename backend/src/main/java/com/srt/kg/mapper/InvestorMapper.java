package com.srt.kg.mapper;

import com.srt.kg.entity.Investor;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import java.util.List;

@Mapper
public interface InvestorMapper {
    List<Investor> findAll(@Param("keyword") String keyword, @Param("offset") int offset, @Param("limit") int limit);
    int count(@Param("keyword") String keyword);
    Investor findById(Long id);
    int insert(Investor investor);
}
