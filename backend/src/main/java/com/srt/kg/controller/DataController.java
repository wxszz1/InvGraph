package com.srt.kg.controller;

import com.srt.kg.entity.Enterprise;
import com.srt.kg.entity.Investor;
import com.srt.kg.entity.Industry;
import com.srt.kg.mapper.EnterpriseMapper;
import com.srt.kg.mapper.InvestorMapper;
import com.srt.kg.mapper.IndustryMapper;
import com.srt.kg.mapper.InvestmentEventMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/data")
public class DataController {

    @Autowired
    private EnterpriseMapper enterpriseMapper;
    @Autowired
    private InvestorMapper investorMapper;
    @Autowired
    private IndustryMapper industryMapper;
    @Autowired
    private InvestmentEventMapper investmentEventMapper;

    @GetMapping("/enterprises")
    public Map<String, Object> listEnterprises(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) String keyword) {
        int offset = (page - 1) * size;
        List<Enterprise> list = enterpriseMapper.findAll(keyword, offset, size);
        int total = enterpriseMapper.count(keyword);
        Map<String, Object> result = new HashMap<>();
        result.put("code", 200);
        result.put("msg", "success");
        Map<String, Object> data = new HashMap<>();
        data.put("list", list);
        data.put("total", total);
        data.put("page", page);
        data.put("size", size);
        result.put("data", data);
        return result;
    }

    @GetMapping("/investors")
    public Map<String, Object> listInvestors(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) String keyword) {
        int offset = (page - 1) * size;
        List<Investor> list = investorMapper.findAll(keyword, offset, size);
        int total = investorMapper.count(keyword);
        Map<String, Object> result = new HashMap<>();
        result.put("code", 200);
        result.put("msg", "success");
        Map<String, Object> data = new HashMap<>();
        data.put("list", list);
        data.put("total", total);
        data.put("page", page);
        data.put("size", size);
        result.put("data", data);
        return result;
    }

    @GetMapping("/industries")
    public Map<String, Object> listIndustries() {
        List<Industry> list = industryMapper.findAll();
        Map<String, Object> result = new HashMap<>();
        result.put("code", 200);
        result.put("msg", "success");
        result.put("data", list);
        return result;
    }

    @GetMapping("/enterprise/{id}/history")
    public Map<String, Object> enterpriseHistory(@PathVariable Long id) {
        Enterprise enterprise = enterpriseMapper.findById(id);
        var events = investmentEventMapper.findByEnterpriseIdWithNames(id);
        Map<String, Object> result = new HashMap<>();
        result.put("code", 200);
        result.put("msg", "success");
        Map<String, Object> data = new HashMap<>();
        data.put("enterprise", enterprise);
        data.put("events", events);
        result.put("data", data);
        return result;
    }
}
