package com.srt.kg.mapper;

import com.srt.kg.entity.Enterprise;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import java.util.List;

@Mapper
public interface EnterpriseMapper {
    List<Enterprise> findAll(@Param("keyword") String keyword, @Param("offset") int offset, @Param("limit") int limit);
    int count(@Param("keyword") String keyword);
    Enterprise findById(Long id);
    int insert(Enterprise enterprise);
    int insertBatch(List<Enterprise> list);
}
