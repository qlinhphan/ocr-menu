package com.example.demo.service;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.example.demo.model.Category;
import com.example.demo.model.ItemDescription;
import com.example.demo.model.MenuItem;
import com.example.demo.model.dto.ObjectSave;
import com.example.demo.repo.CategoryRepository;
import com.example.demo.repo.ItemDescriptionRepository;
import com.example.demo.repo.MenuItemRepository;

@Service
public class CreateMenuService {

    @Autowired
    private CategoryRepository categoryRepository;

    @Autowired
    private MenuItemRepository menuItemRepository;

    @Autowired
    private ItemDescriptionRepository itemDescriptionRepository;

    public ObjectSave createMenu(ObjectSave objectSave) {
        Category category = new Category();
        category.setName(objectSave.getName_cate());

        List<String> name_cates = this.categoryRepository.findAll().stream().map(Category::getName).toList();
        if (!name_cates.contains(objectSave.getName_cate())) {
            Category cateSaved = this.categoryRepository.save(category);

            MenuItem menuItem = new MenuItem();
            menuItem.setName(objectSave.getName_menu());
            menuItem.setCategory(cateSaved);
            MenuItem menuItemSaved = this.menuItemRepository.save(menuItem);

            ItemDescription itemDescription = new ItemDescription();
            itemDescription.setDescription(objectSave.getDescription_item());
            itemDescription.setOptional(objectSave.getOptional_item());
            itemDescription.setPrice(objectSave.getPrice_item());
            itemDescription.setSize(objectSave.getSize_item());
            itemDescription.setMenuItem(menuItemSaved);
            this.itemDescriptionRepository.save(itemDescription);

            return objectSave;
        } else {
            // Category cateSaved = this.categoryRepository.save(category);

            MenuItem menuItem = new MenuItem();
            menuItem.setName(objectSave.getName_menu());
            menuItem.setCategory(this.categoryRepository.findByName(objectSave.getName_cate()));
            MenuItem menuItemSaved = this.menuItemRepository.save(menuItem);

            ItemDescription itemDescription = new ItemDescription();
            itemDescription.setDescription(objectSave.getDescription_item());
            itemDescription.setOptional(objectSave.getOptional_item());
            itemDescription.setPrice(objectSave.getPrice_item());
            itemDescription.setSize(objectSave.getSize_item());
            itemDescription.setMenuItem(menuItemSaved);
            this.itemDescriptionRepository.save(itemDescription);

            return objectSave;
        }

    }

}
