package com.example.demo.controller;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.web.bind.annotation.RestController;

import com.example.demo.model.ImgHist;
import com.example.demo.model.dto.ResponsePageHist;
import com.example.demo.repo.ImgHistRepository;

import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;

@RestController
@CrossOrigin(origins = "http://localhost:5173")
public class HistController {
    @Autowired
    private ImgHistRepository imgHistRepository;

    @GetMapping("/hist-extract")
    public ResponsePageHist getMethodName(@RequestParam("limit") int limit, @RequestParam("page") int page) {
        Pageable pageable = PageRequest.of(page - 1, limit);
        Page<ImgHist> hists = this.imgHistRepository.findAll(pageable);
        List<ImgHist> lisHists = hists.getContent();

        ResponsePageHist res = new ResponsePageHist();
        res.setSumPage(hists.getTotalPages());
        res.setSumTotal(lisHists.size());
        res.setHists(lisHists);

        return res;
    }

}
