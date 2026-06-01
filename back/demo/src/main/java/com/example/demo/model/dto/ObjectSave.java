package com.example.demo.model.dto;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class ObjectSave {
    private String name_cate;

    private String name_menu;
    private Long cate_id;

    private String description_item;
    private String optional_item;
    private Integer price_item;
    private String size_item;
    private Long menu_item_id;
}
