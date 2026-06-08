package com.example.demo.repo;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import com.example.demo.model.ImgHist;

public interface ImgHistRepository extends JpaRepository<ImgHist, Long> {
    public Page<ImgHist> findAll(Pageable pageable);
}
