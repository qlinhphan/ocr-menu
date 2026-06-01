package com.example.demo.repo;

import org.springframework.data.jpa.repository.JpaRepository;

import com.example.demo.model.ItemDescription;

public interface ItemDescriptionRepository extends JpaRepository<ItemDescription, Long> {

}
