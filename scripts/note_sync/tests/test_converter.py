#!/usr/bin/env python3
"""
测试核心转换功能
"""

import json
import pytest
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from converter import HugoToObsidianConverter, ObsidianToHugoConverter


@pytest.fixture
def test_data():
    """测试数据"""
    # Hugo 格式的测试数据
    hugo_content = """+++
title = "Test Note"
author = ["CC"]
date = 2023-11-18T22:27:00+08:00
slug = "test"
tags = ["test", "example"]
categories = ["note", "tech"]
draft = false
toc = true
+++

# Test Content

This is a test note.
"""

    # Obsidian 格式的测试数据
    obsidian_content = """---
title: Test Note
type:
  - note
  - tech
aliases:
tags:
  - test
  - example
date: 2023-11-18
ts: 20231118222700
draft: false
---

# Test Content

This is a test note.
"""
    hugo_to_obsidian_mapping = """{
  "direction": "hugo-to-obsidian",
  "mapping": {
    "title": {
      "target": "title",
      "type": "string"
    },
    "date": {
      "target": "date",
      "type": "date"
    },
    "tags": {
      "target": "tags",
      "type": "array"
    },
    "categories": {
      "target": "type",
      "type": "array"
    },
    "draft": {
      "target": "draft",
      "type": "boolean"
    }
  }
}"""
    obsidian_to_hugo_mapping = """{
  "direction": "obsidian-to-hugo",
  "mapping": {
      "title": {
      "target": "title",
      "type": "string"
    },
    "type": {
      "target": "categories",
      "type": "array"
    },
    "tags": {
      "target": "tags",
      "type": "array"
    },
    "date": {
      "target": "date",
      "type": "date"
    },
    "draft": {
      "target": "draft",
      "type": "boolean"
    }
  }
}"""
    return {
        "hugo_content": hugo_content,
        "obsidian_content": obsidian_content,
        "hugo_to_obsidian_mapping": hugo_to_obsidian_mapping,
        "obsidian_to_hugo_mapping": obsidian_to_hugo_mapping,
    }


def test_hugo_to_obsidian(test_data):
    """测试 Hugo 到 Obsidian 的转换"""
    field_mapping = json.loads(test_data["hugo_to_obsidian_mapping"])
    converter = HugoToObsidianConverter(field_mapping=field_mapping)
    result = converter.convert(test_data["hugo_content"])

    # 验证转换结果包含必要字段
    assert "type:" in result
    assert "note" in result
    assert "tech" in result
    assert "tags:" in result
    assert "test" in result
    assert "example" in result
    assert "date: 2023-11-18" in result
    assert "draft: false" in result
    assert "# Test Content" in result


def test_obsidian_to_hugo(test_data):
    """测试 Obsidian 到 Hugo 的转换"""
    field_mapping = json.loads(test_data["obsidian_to_hugo_mapping"])
    converter = ObsidianToHugoConverter(field_mapping=field_mapping)
    result = converter.convert(test_data["obsidian_content"])

    # 验证转换结果包含必要字段
    assert 'title = "Test Note"' in result
    assert "date = 2023-11-18" in result
    assert 'tags = ["test", "example"]' in result
    assert 'categories = ["note", "tech"]' in result
    assert "draft = false" in result
    assert "# Test Content" in result


def test_field_mapping(test_data):
    """测试字段映射功能"""
    # 测试自定义字段映射
    custom_mapping = {
        "direction": "hugo-to-obsidian",
        "mapping": {
            "title": {"target": "title", "type": "string"},
            "date": {"target": "date", "type": "date"},
            "tags": {"target": "tags", "type": "array"},
            "categories": {"target": "type", "type": "array"},
            "draft": {"target": "draft", "type": "boolean"},
        },
    }

    converter = HugoToObsidianConverter(field_mapping=custom_mapping)
    result = converter.convert(test_data["hugo_content"])

    # 验证自定义映射是否生效
    assert "type:" in result
    assert "note" in result
    assert "tech" in result