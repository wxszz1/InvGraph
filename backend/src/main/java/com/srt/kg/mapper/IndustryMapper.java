package com.srt.kg.mapper;

import com.srt.kg.entity.Industry;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import java.util.List;

@Mapper
public interface IndustryMapper {
    List<Industry> findAll();
    Industry findById(Long id);
    Industry findByName(String name);
    int insert(Industry industry);
}
