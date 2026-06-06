"""
项目配置加载模块
从 config/config.yaml 读取配置，提供全局统一的路径和参数访问
"""

import os
import yaml
from pathlib import Path


def load_config(config_path: str = None) -> dict:
    """加载 YAML 配置文件"""
    if config_path is None:
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "config",
            "config.yaml",
        )

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 将相对路径解析为绝对路径
    root = Path(config["paths"]["root"])
    for key, rel_path in config["paths"].items():
        if key != "root":
            config["paths"][key] = str(root / rel_path)

    return config


def get_data_path(config: dict, category: str, filename: str) -> str:
    """
    获取指定数据文件的完整路径

    参数:
        config: 配置字典
        category: 类别 (population, healthcare, sentiment, geo)
        filename: 文件名 (可选，若不提供则使用配置中的默认文件)
    """
    base = config["paths"]["data_raw"]
    return os.path.join(base, category, filename)


def ensure_dirs(config: dict):
    """确保所有输出目录存在"""
    for key in ["output_figures", "output_reports", "output_tables"]:
        path = config["paths"].get(key)
        if path:
            os.makedirs(path, exist_ok=True)


# 单例配置
_config = None


def get_config() -> dict:
    """获取全局配置（单例）"""
    global _config
    if _config is None:
        _config = load_config()
    return _config
