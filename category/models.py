#! -*- coding:utf-8 -*-
from django.db import models
from category.manager import AdaptorCategoryManager 


class Category(models.Model):
    """类别模型"""
    TOP_LEVEL = 1 
    name = models.CharField(max_length = 1024)
    # 分类
    level = models.IntegerField(default = TOP_LEVEL) 
    # 顶级分类可以没有父类别
    parent = models.ForeignKey('Category', on_delete=models.CASCADE , null = True)
    objects = AdaptorCategoryManager()  
    entity = models.SmallIntegerField(null = True)
    # 类别图片
    icon = models.CharField(max_length = 1024, null=True)
    # 是否可见
    visible = models.PositiveSmallIntegerField(default= 1)

    # 0 默认表示民宿类型，1表示景区门票，2、租车  10其他
    categorytype = models.PositiveSmallIntegerField(default= 0)
     
    
    # 排序
    sort = models.PositiveSmallIntegerField(default= 1)

    def __str__(self):
        return self.name
    
    class Meta:
        default_permissions = () 
        constraints = [
            models.UniqueConstraint(fields = ['name', 'level', "parent"], 
            name = "category_unique")
        ]
        ordering = ["sort"]

