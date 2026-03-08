#!/usr/bin/env python3
"""
主应用文件，实现 web 服务
"""

import traceback

from flask import Flask, request, render_template, jsonify
import os
import tempfile
import json
import re
from converter import (
    do_convert,
    normalize_path,
    collect_markdown_files,
    convert_content,
)


app = Flask(__name__)

# 获取当前文件所在目录的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = tempfile.gettempdir()
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ==================== 共用工具方法 ====================


def _get_field_mapping() -> dict | None:
    """从请求中获取和解析字段映射，并提取direction"""
    mapping_str = request.form.get("mapping")
    if not mapping_str:
        return None
    try:
        data = json.loads(mapping_str)
        app.logger.warning(f"原始字段映射: {data}")
        # 如果是完整的配置（包含direction和mapping），则返回配置
        if isinstance(data, dict) and "direction" in data and "mapping" in data:
            return data
    except:
        app.logger.error("字段映射解析失败")
    return None


# ==================== 路由处理 ====================


@app.route("/")
def index():
    """首页"""
    return render_template("index.html")


@app.route("/convert", methods=["POST"])
def convert():
    """转换文件"""
    try:
        input_path = request.form.get("input_path")
        if not input_path:
            return jsonify({"error": "文件路径不能为空"}), 400

        # 标准化路径
        input_path = normalize_path(input_path)
        if not input_path or not os.path.exists(input_path):
            return jsonify({"error": "输入路径不存在"}), 400

        # 处理输出路径
        output_path = request.form.get("output_path") or "../../content"
        output_path = normalize_path(output_path)
        if not output_path:
            return jsonify({"error": "输出路径解析失败"}), 400
        os.makedirs(output_path, exist_ok=True)

        # 获取字段映射，并从中提取direction
        field_mapping = _get_field_mapping()

        if field_mapping is None:
            return jsonify({"error": "字段映射解析失败"}), 400

        if not field_mapping.get("direction"):
            return jsonify({"error": "转换方向不能为空"}), 400

        # 是否确认覆盖已存在文件
        overwrite = request.form.get("overwrite") == "true"

        # 执行转换
        success, error_type, message = do_convert(
            input_path, output_path, field_mapping, overwrite
        )

        if success is False:
            if error_type == "duplicated":
                # 如果有重名文件且未确认覆盖，返回确认请求
                return jsonify({"overwrite_confirm": True, "files": message})
            elif error_type == "no_markdown":
                return jsonify({"error": "未找到 Markdown 文件"}), 400
            return jsonify({"error": message}), 400

        return jsonify(
            {"success": True, "files": message, "output_path": output_path}
        )

    except ValueError as e:
        app.logger.error(f"转换失败: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app.logger.error(f"转换失败: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


@app.route("/preview", methods=["POST"])
def preview():
    """预览转换结果"""
    try:
        input_path = request.form.get("input_path")
        if not input_path:
            return jsonify({"error": "文件路径不能为空"}), 400

        # 标准化路径
        input_path = normalize_path(input_path)
        if not input_path or not os.path.exists(input_path):
            return jsonify({"error": "文件路径不存在"}), 400

        # 获取字段映射，并从中提取direction
        field_mapping = _get_field_mapping()

        if not field_mapping:
            return jsonify({"error": "字段映射解析失败"}), 400

        if not field_mapping.get("direction"):
            return jsonify({"error": "转换方向不能为空"}), 400

        # 收集 Markdown 文件
        md_files, is_directory = collect_markdown_files(input_path)

        if not md_files:
            return jsonify({"error": "未找到 Markdown 文件"}), 400

        # 获取第一个文件进行预览
        preview_file = os.path.join(md_files[0][0], md_files[0][1], md_files[0][2])
        with open(preview_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 执行转换
        converted_content = convert_content(content, field_mapping)

        # 返回结果
        result: dict = {"content": converted_content, "source_content": content}

        # 如果是目录，返回目录信息
        if is_directory:
            result["directory"] = True
            result["files"] = md_files

        return jsonify(result)

    except ValueError as e:
        app.logger.error(f"预览转换失败: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app.logger.error(f"预览转换失败: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


@app.route("/save-template", methods=["POST"])
def save_template():
    """保存模板"""
    try:
        # 获取模板名称
        template_name = request.form.get("template_name")
        if not template_name:
            return jsonify({"error": "模板名称不能为空"}), 400

        # 获取转换方向
        direction = request.form.get("direction")
        if not direction:
            return jsonify({"error": "转换方向不能为空"}), 400

        # 获取映射
        mapping_str = request.form.get("mapping")
        if not mapping_str:
            return jsonify({"error": "映射不能为空"}), 400

        # 解析映射
        try:
            mapping = json.loads(mapping_str)
        except:
            return jsonify({"error": "映射格式错误"}), 400

        # 确保 data 目录存在
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(data_dir, exist_ok=True)

        # 保存模板
        template_path = os.path.join(data_dir, f"{template_name}.json")
        with open(template_path, "w", encoding="utf-8") as f:
            json.dump(
                {"direction": direction, "mapping": mapping},
                f,
                ensure_ascii=False,
                indent=2,
            )

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/get-default-mapping/<direction>")
def get_default_mapping(direction):
    """获取默认的字段映射"""
    try:
        # 验证转换方向
        if direction not in ["hugo-to-obsidian", "obsidian-to-hugo"]:
            return jsonify({"error": "无效的转换方向"}), 400

        # 加载默认映射文件
        mapping_file = os.path.join(
            os.path.dirname(__file__), "templates", "mappings", f"{direction}.json"
        )
        if not os.path.exists(mapping_file):
            return jsonify({"error": "默认映射文件不存在"}), 400

        with open(mapping_file, "r", encoding="utf-8") as f:
            mapping_data = json.load(f)

        return jsonify(
            {
                "direction": mapping_data.get("direction"),
                "mapping": mapping_data.get("mapping"),
                "is_default": True,
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/get-templates")
def get_templates():
    """获取模板列表（用户模板和默认模板分别返回）"""
    try:
        # 用户模板目录
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(data_dir, exist_ok=True)

        # 获取用户模板列表
        user_templates = []
        if os.path.exists(data_dir):
            for file in os.listdir(data_dir):
                if file.endswith(".json"):
                    user_templates.append(
                        {"name": os.path.splitext(file)[0], "is_default": False}
                    )

        # 获取默认模板列表
        default_templates = []
        mappings_dir = os.path.join(os.path.dirname(__file__), "templates", "mappings")
        if os.path.exists(mappings_dir):
            for file in os.listdir(mappings_dir):
                if file.endswith(".json"):
                    # 去掉扩展名，转换为友好名称
                    template_name = os.path.splitext(file)[0]
                    default_templates.append(
                        {"name": template_name, "is_default": True}
                    )

        return jsonify(
            {"user_templates": user_templates, "default_templates": default_templates}
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/load-template", methods=["POST"])
def load_template():
    """加载模板"""
    try:
        # 获取模板名称和是否为默认模板
        template_name = request.form.get("template_name")
        is_default = request.form.get("is_default") == "true"

        if not template_name:
            return jsonify({"error": "模板名称不能为空"}), 400

        if is_default:
            # 加载默认模板（从 templates/mappings/ 目录）
            # 支持加载特定方向的映射
            mapping_file = os.path.join(
                os.path.dirname(__file__),
                "templates",
                "mappings",
                f"{template_name}.json",
            )
        else:
            # 加载用户模板（从 data/ 目录）
            # 确保 data 目录存在
            data_dir = os.path.join(os.path.dirname(__file__), "data")
            os.makedirs(data_dir, exist_ok=True)
            mapping_file = os.path.join(data_dir, f"{template_name}.json")

        if not os.path.exists(mapping_file):
            return jsonify({"error": "模板不存在"}), 400

        with open(mapping_file, "r", encoding="utf-8") as f:
            template = json.load(f)

        return jsonify({"template": template, "is_default": is_default})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # 确保 templates 目录存在
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    if not os.path.exists(template_dir):
        os.makedirs(template_dir)

    # 启动应用
    app.run(debug=True, host="0.0.0.0", port=5000)
