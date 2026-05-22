package com.srt.kg.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import com.alibaba.fastjson.JSONArray;
import com.alibaba.fastjson.JSONObject;

@Service
public class NlpClientService {

    @Value("${nlp.service.url}")
    private String nlpUrl;

    private final RestTemplate restTemplate = new RestTemplate();

    public JSONObject extractEntitiesAndRelations(String text) {
        JSONObject request = new JSONObject();
        request.put("text", text);
        try {
            String response = restTemplate.postForObject(nlpUrl + "/api/extract", request, String.class);
            return JSONObject.parseObject(response);
        } catch (Exception e) {
            JSONObject fallback = new JSONObject();
            fallback.put("entities", new JSONArray());
            fallback.put("relations", new JSONArray());
            fallback.put("triples", new JSONArray());
            fallback.put("error", "NLP服务不可用: " + e.getMessage());
            return fallback;
        }
    }
}
