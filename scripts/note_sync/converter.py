#!/usr/bin/env python3
"""
核心转换功能实现
"""

from dataclasses import dataclass
from logging import getLogger
import re
import os
from datetime import datetime
from typing import Any

log = getLogger(__name__)
log.setLevel("DEBUG")

TypeArray = "array"
TypeString = "string"
TypeBoolean = "boolean"
TypeDate = "date"


@dataclass
class Field:
    """字段映射类"""

    key: str = ""
    val: Any = None
    ftype: str = TypeString  # 默认类型为字符串


@dataclass
class MappingRule:
    """字段映射规则类"""

    source: str
    target: str
    ftype: str


HUGO_DEFAULT_HEADERS = [
    ("title", "", TypeString),
    ("author", "CC", TypeString),
    ("date", datetime.now(), TypeDate),
    ("tags", [], TypeArray),
    ("categories", [], TypeArray),
    ("draft", False, TypeBoolean),
    ("toc", True, TypeBoolean),
]


class ConverterMixin:
    """转换器 Mixin 类，提供共用方法"""

    def load_mapping_rule(self, data: dict) -> dict[str, MappingRule]:
        """加载映射规则"""
        rules = {}
        for source, mapping in data.items():
            if isinstance(mapping, dict):
                # 格式：{target: '...', type: '...'}
                if not mapping.get("target") or not mapping.get("type"):
                    continue  # 跳过无效的映射
                rules[source] = MappingRule(
                    source=source,
                    target=mapping.get("target", ""),
                    ftype=mapping.get("type", TypeString),
                )
        return rules

    def transfer_fields(
        self,
        field_mapping: dict[str, MappingRule],
        source_fields: list[Field],
    ) -> list[Field]:
        """根据映射规则转换字段

        Args:
            field_mapping: 字段映射规则
            source_fields: 源字段列表

        Returns:
            list[Field]: 转换后的目标字段列表
        """
        target_fields = []
        for field in source_fields:
            field_map: MappingRule | None = field_mapping.get(field.key)
            if field_map and field_map.ftype == field.ftype:
                target_fields.append(
                    Field(key=field_map.target, val=field.val, ftype=field.ftype)
                )
        return target_fields

    def extract_body(self, content: str, header_mark: str = "") -> str:
        """提取正文内容，去除前端部分"""
        if not header_mark:
            return content.strip()

        content_match = re.search(
            rf"^{header_mark}.*?{header_mark}(.*)", content, re.DOTALL
        )
        if content_match:
            return content_match.group(1).strip()
        else:
            return content


class HugoToObsidianConverter(ConverterMixin):
    """Hugo 到 Obsidian 的转换器"""

    def __init__(self, field_mapping: dict):
        """初始化转换器

        Args:
            field_mapping: 自定义字段映射
        """
        self.direction = field_mapping.get("direction")
        mapping_data = field_mapping.get("mapping", {})
        self.field_mapping: dict[str, MappingRule] = self.load_mapping_rule(
            mapping_data
        )

        self.title = ""
        self.source_fields: list[Field] = []
        self.target_fields: list[Field] = []
        self.header_mark: str = r"\+\+\+"
        self.is_draft: bool = False

    def parse_source_header(self, content: str) -> list[Field]:
        """解析 Hugo 前端

        Args:
            content: Hugo 格式的内容

        Returns:
            dict: 解析后的字段
        """
        frontmatter_match = re.match(
            rf"^{self.header_mark}(.*?){self.header_mark}",
            content,
            re.DOTALL,
        )
        if not frontmatter_match:
            return []

        header = frontmatter_match.group(1)
        fields: list[Field] = []
        for line in header.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, raw_val = line.split("=", 1)
            raw_val = raw_val.strip()
            key = key.strip()
            new_field = Field(key=key)
            if (raw_val.startswith('"') and raw_val.endswith('"')) or (
                raw_val.startswith("'") and raw_val.endswith("'")
            ):
                # String 类型，去除引号
                new_field.val = raw_val.strip(" \"'")
                new_field.ftype = TypeString
            elif raw_val.lower() in ["true", "false"]:
                # Boolean 类型
                new_field.val = raw_val.lower() == "true"
                new_field.ftype = TypeBoolean
            elif raw_val.startswith("[") and raw_val.endswith("]"):
                # Array 类型，去除方括号并分割
                new_field.ftype = TypeArray
                raw_val = raw_val.strip("[]")
                items = raw_val.split(",")
                new_field.val = []
                for item in items:
                    item = item.strip(" \"'")
                    new_field.val.append(item)
            elif re.match(
                r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}$", raw_val
            ):
                # Date 类型，转换为 datetime 对象
                new_field.val = datetime.fromisoformat(raw_val)
                new_field.ftype = TypeDate
            else:
                # 其他类型，默认字符串
                new_field.val = raw_val
                new_field.ftype = TypeString
            fields.append(new_field)
            # 提取草稿字段
            if new_field.key == "draft":
                self.is_draft = new_field.val
            # 提取标题字段
            if key == "title":
                self.title = new_field.val
        return fields

    def format_fields(self, fields: list[Field]) -> str:
        """格式化字段列表为 Obsidian 前端字符串

        Args:
            fields: 字段列表

        Returns:
            str: 格式化后的前端字符串
        """
        # 生成 Obsidian 前端字符串
        formatted = ["---"]
        for field in fields:
            if field.ftype == TypeString:
                formatted.append(f"{field.key}: {field.val}")
            elif field.ftype == TypeBoolean:
                formatted.append(f"{field.key}: {str(field.val).lower()}")
            elif field.ftype == TypeArray:
                formatted.append(f"{field.key}:")
                for item in field.val:
                    formatted.append(f"  - {item}")
            elif field.ftype == TypeDate:
                formatted.append(f"{field.key}: {field.val.strftime('%Y-%m-%d')}")
        formatted.append("---")
        return "\n".join(formatted)

    def convert_header(self, content):
        """转换 Obsidian 前端为 Hugo 前端"""
        # 解析 Obsidian 前端
        self.source_fields = self.parse_source_header(content)

        # 构建 Hugo 前端
        self.target_fields = self.transfer_fields(
            self.field_mapping, self.source_fields
        )

        # 生成 Hugo 前端字符串
        header = self.format_fields(self.target_fields)
        log.info(f"转换前端字段: {self.source_fields} -> {self.target_fields}")
        return header

    def convert_body(self, content):
        """转换正文内容"""
        body = self.extract_body(content, self.header_mark)
        return body + "\n"  # 确保正文末尾有换行符

    def convert(self, content):
        """执行转换

        Args:
            content: Hugo 格式的内容

        Returns:
            str: Obsidian 格式的内容
        """
        header = self.convert_header(content)

        hugo_body = self.convert_body(content)

        return header + "\n\n" + hugo_body

    def convert_file(self, file_path):
        """转换文件内容

        Args:
            file_path: 输入文件路径

        Returns:
            str: 转换后的内容
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return self.convert(content)


class ObsidianToHugoConverter(ConverterMixin):
    """Obsidian 到 Hugo 的转换器"""

    def __init__(self, field_mapping: dict):
        """初始化转换器

        Args:
            field_mapping: 自定义字段映射
        """
        self.direction = field_mapping.get("direction")
        mapping_data = field_mapping.get("mapping", {})
        self.field_mapping: dict[str, MappingRule] = self.load_mapping_rule(
            mapping_data
        )

        self.title: str = ""
        self.source_fields: list[Field] = []
        self.target_fields: list[Field] = []
        self.header_mark: str = "---"
        self.is_draft: bool = False

    def parse_source_header(self, content: str) -> list[Field]:
        """解析 Obsidian 前端

        Args:
            content: Obsidian 格式的内容

        Returns:
            dict: 解析后的字段
        """
        frontmatter_match = re.match(
            rf"^{self.header_mark}(.*?){self.header_mark}",
            content,
            re.DOTALL,
        )
        if not frontmatter_match:
            return []
        
        header = frontmatter_match.group(1).strip()
        log.warning(f"obsidian header: {header}")
        fields: list[Field] = []
        lines = header.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            i += 1

            if not line or line.startswith("#"):
                continue
            key, raw_val = line.split(":", 1)
            raw_val = raw_val.strip()
            key = key.strip()
            new_field = Field(key=key)
            if (raw_val.startswith('"') and raw_val.endswith('"')) or (
                raw_val.startswith("'") and raw_val.endswith("'")
            ):
                # String 类型，去除引号
                new_field.val = raw_val.strip(" \"'")
                new_field.ftype = TypeString
            elif raw_val.lower() in ["true", "false"]:
                # Boolean 类型
                new_field.val = raw_val.lower() == "true"
                new_field.ftype = TypeBoolean
            elif not raw_val:
                # 可能是 Array 类型，向下查找列表项
                # 查找后续的列表项
                while i < len(lines):
                    next_line = lines[i].strip()
                    if next_line.startswith("- "):
                        if not new_field.val:
                            new_field.ftype = TypeArray
                            new_field.val = []
                        new_field.val.append(next_line.strip("- \"'"))
                        i += 1
                    else:
                        break
            elif re.match(r"^\d{4}-\d{2}-\d{2}$", raw_val):
                # Date 类型，转换为 datetime 对象
                new_field.val = datetime.strptime(raw_val, "%Y-%m-%d")
                new_field.ftype = TypeDate
            else:
                # 其他类型，默认字符串
                new_field.val = raw_val
                new_field.ftype = TypeString
            # 提取草稿字段
            if new_field.key == "draft":
                log.warning(f"草稿字段: {new_field.key} = {new_field.val}")
                self.is_draft = new_field.val
            # 提取标题字段 优先使用 title 属性
            if key == "title" and new_field.val:
                self.title = new_field.val
            fields.append(new_field)
        return fields

    def format_fields(self, fields: list[Field]) -> str:
        """格式化字段列表为 Hugo 前端字符串

        Args:
            fields: 字段列表

        Returns:
            str: 格式化后的 Hugo 前端字符串
        """
        # 将默认字段与转换后的字段合并，确保默认字段存在且顺序正确
        new_fields = []
        fields_dict = {field.key: field for field in fields}
        for key, default_val, ftype in HUGO_DEFAULT_HEADERS:
            field = fields_dict.pop(key, None)
            if not field:
                field = Field(key=key, val=default_val, ftype=ftype)
            if key == "title" and self.title:
                field.val = self.title
            new_fields.append(field)

        new_fields.extend(fields_dict.values())  # 添加剩余的自定义字段

        # 生成 Hugo 前端字符串
        formatted = ["+++"]
        for field in new_fields:
            if field.ftype == TypeString:
                formatted.append(f'{field.key} = "{field.val}"')
            elif field.ftype == TypeBoolean:
                formatted.append(f"{field.key} = {str(field.val).lower()}")
            elif field.ftype == TypeArray:
                items_str = ", ".join([f'"{item}"' for item in field.val])
                formatted.append(f"{field.key} = [{items_str}]")
            elif field.ftype == TypeDate:
                formatted.append(
                    f"{field.key} = {field.val.strftime('%Y-%m-%dT%H:%M:%S%z')}"
                )
        formatted.append("+++")
        return "\n".join(formatted)

    def convert_header(self, content):
        """转换 Obsidian 前端为 Hugo 前端"""
        # 解析 Obsidian 前端
        self.source_fields = self.parse_source_header(content)

        # 构建 Hugo 前端
        self.target_fields = self.transfer_fields(
            self.field_mapping, self.source_fields
        )

        # 生成 Hugo 前端字符串
        header = self.format_fields(self.target_fields)
        return header

    def convert_body(self, content):
        """转换正文内容"""
        body = self.extract_body(content, self.header_mark)
        return body + "\n"  # 确保正文末尾有换行符

    def convert(self, content: str) -> str:
        """执行转换

        Args:
            content: Obsidian 格式的内容

        Returns:
            str: Hugo 格式的内容
        """
        header = self.convert_header(content)

        hugo_body = self.convert_body(content)

        return header + "\n\n" + hugo_body

    def convert_file(self, file_path: str) -> str:
        """转换文件内容

        Args:
            file_path: 输入文件路径

        Returns:
            str: 转换后的内容
        """
        self.title = os.path.splitext(os.path.basename(file_path))[0]
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        return self.convert(content)


# ==================== 共用工具方法 ====================


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def normalize_path(path: str) -> str:
    """标准化路径：移除引号并转换为绝对路径"""
    if not path:
        return ""
    # 移除路径两端的引号
    path = re.sub(r"^[\'\"]|[\'\"]$", "", path)
    # 处理相对路径
    if not os.path.isabs(path):
        path = os.path.join(PROJECT_ROOT, path)
    return path


def collect_markdown_files(path) -> tuple[list[tuple[str, str, str]], bool]:
    """
    收集指定路径下的所有 Markdown 文件
    返回: (md_files, is_directory) 元组
    """
    md_files: list[tuple[str, str, str]] = []  # (root_path, relative_dir, filename)
    is_directory = False

    # 嵌套目录需要 保留子目录结构
    if os.path.isfile(path):
        if path.endswith(".md") and os.path.basename(path) != "_index.md":
            md_files.append((os.path.dirname(path), '', os.path.basename(path)))
        else:
            raise ValueError("只支持 Markdown 文件")
    elif os.path.isdir(path):
        is_directory = True
        for dirname, subdirs, files in os.walk(path):
            relative_path = os.path.relpath(dirname, path)
            for file in files:
                if file.endswith(".md") and file != "_index.md":
                    md_files.append((path, relative_path, file))
    else:
        raise ValueError("无效的文件路径")

    if not md_files:
        raise ValueError("没有找到 Markdown 文件")

    return md_files, is_directory


def get_converter(field_mapping):
    direction = field_mapping.get("direction")
    if not direction or direction not in ["hugo-to-obsidian", "obsidian-to-hugo"]:
        raise ValueError("无效的转换方向")

    if direction == "hugo-to-obsidian":
        converter = HugoToObsidianConverter(field_mapping=field_mapping)
    else:
        converter = ObsidianToHugoConverter(field_mapping=field_mapping)
    return converter


def convert_content(content, field_mapping):
    """转换文件内容"""
    converter = get_converter(field_mapping)
    return converter.convert(content)


def do_convert(
    input_path,
    output_path,
    field_mapping,
    overwrite=False,
    preview=False,
) -> tuple[bool, str, str | list[str]]:
    """
    执行转换

    Args:
        input_path: 输入文件或目录路径
        output_path: 输出目录路径
        field_mapping: 字段映射规则
        overwrite: 是否覆盖已存在文件

    Returns:
        tuple: (success, error_type, error_message)
            success: 转换是否成功
            error_type: 错误类型（如 "duplicated"）
            error_message: 错误信息或相关数据
    """
    # 标准化路径
    input_path = normalize_path(input_path)
    output_path = normalize_path(output_path)
    log.warning(f"开始转换: {input_path} -> {output_path}")

    if not input_path or not os.path.exists(input_path):
        return False, "invalid_input", "输入路径不存在"

    converter = get_converter(field_mapping)

    # 收集 Markdown 文件
    md_files, is_directory = collect_markdown_files(input_path)
    log.warning(f"发现 {len(md_files)} 个 Markdown 文件: {md_files}")
    if not md_files:
        return False, "no_markdown", "未找到 Markdown 文件"

    # 进行转换
    existing_files = []
    results = []
    for root_path, relative_path, filename in md_files:
        filename = os.path.join(root_path, relative_path, filename)
        content = converter.convert_file(filename)

        output_file_path = os.path.join(output_path, relative_path, converter.title + ".md")
        if os.path.exists(output_file_path):
            existing_files.append(output_file_path)
        if converter.is_draft is True:
            log.warning(f"草稿文件: {filename} skip")
            continue
        results.append((content, output_file_path))
    log.warning(f"转换完成: {len(results)} 个文件")
    if existing_files and not overwrite:
        return False, "duplicated", existing_files

    # 如果是预览模式，只返回转换结果
    if preview:
        return True, "", [content for content, _ in results]

    # 保存转换结果
    log.warning(f"开始保存")
    for content, output_file_path in results:
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(content)
            log.warning(f"保存完成: {output_file_path}")

    file_list = [output_file_path for _, output_file_path in results]
    return True, "", file_list
