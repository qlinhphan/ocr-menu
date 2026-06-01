package com.example.demo.controller;

import org.springframework.web.bind.annotation.RestController;

import com.example.demo.model.dto.ObjectSave;
import com.example.demo.model.service.CreateMenuService;

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

}
