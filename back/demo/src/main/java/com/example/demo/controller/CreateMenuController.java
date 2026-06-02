package com.example.demo.controller;

import org.springframework.web.bind.annotation.RestController;

import com.example.demo.model.ImgHist;
import com.example.demo.model.dto.ObjectSave;
import com.example.demo.repo.ImgHistRepository;
import com.example.demo.service.CreateMenuService;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;

@RestController
@CrossOrigin(origins = "http://localhost:5173")
public class CreateMenuController {

    @Autowired
    private CreateMenuService createMenuService;

    @PostMapping("/create-menu")
    public ObjectSave postMethodName(@RequestBody ObjectSave objectSave) {
        return this.createMenuService.createMenu(objectSave);
    }

    @PostMapping("/add-history")
    public String postMethodName(@RequestBody ImgHist imgHist) {
        ImgHist img = new ImgHist();
        img.setName_img(imgHist.getName_img());
        this.createMenuService.saveImgHistory(imgHist);
        return "add successfully!";
    }

}
