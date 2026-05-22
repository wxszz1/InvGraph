package com.srt.kg.controller;

import com.srt.kg.service.NlpClientService;
import com.alibaba.fastjson.JSONObject;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class ExtractController {

    @Autowired
    private NlpClientService nlpClientService;

    @PostMapping("/extract")
    public Map<String, Object> extract(@RequestBody Map<String, Object> body) {
        String text = (String) body.get("text");
        JSONObject result = nlpClientService.extractEntitiesAndRelations(text);
        Map<String, Object> response = new HashMap<>();
        response.put("code", 200);
        response.put("msg", "success");
        response.put("data", result);
        return response;
    }
}
