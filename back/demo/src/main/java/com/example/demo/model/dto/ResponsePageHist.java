package com.example.demo.model.dto;

import java.util.List;

import com.example.demo.model.ImgHist;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class ResponsePageHist {
    private int sumPage;
    private int sumTotal;
    private List<ImgHist> hists;
}
