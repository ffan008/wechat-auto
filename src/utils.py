"""
工具函数
"""
import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from dotenv import load_dotenv

load_dotenv()


def load_config(config_file: str = "config/config.yaml") -> Dict[str, Any]:
    """
    加载配置文件

    Args:
        config_file: 配置文件路径

    Returns:
        配置字典
    """
    config_path = Path(__file__).parent.parent / config_file

    if not config_path.exists():
        return {}

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_prompts(prompts_file: str = "config/prompts.yaml") -> Dict[str, Any]:
    """
    加载提示词模板

    Args:
        prompts_file: 提示词文件路径

    Returns:
        提示词字典
    """
    prompts_path = Path(__file__).parent.parent / prompts_file

    if not prompts_path.exists():
        return {}

    with open(prompts_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def setup_logging(log_level: str = "INFO", log_dir: str = "logs"):
    """
    设置日志

    Args:
        log_level: 日志级别
        log_dir: 日志目录
    """
    # 创建日志目录
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # 配置日志格式
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # 设置日志级别
    level = getattr(logging, log_level.upper(), logging.INFO)

    # 配置根日志记录器
    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            # 控制台输出
            logging.StreamHandler(),
            # 文件输出
            logging.FileHandler(
                log_path / f"{datetime.now().strftime('%Y%m%d')}.log",
                encoding="utf-8"
            )
        ]
    )


def get_env_var(key: str, default: Optional[str] = None) -> str:
    """
    获取环境变量

    Args:
        key: 环境变量名
        default: 默认值

    Returns:
        环境变量值
    """
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"环境变量 {key} 未设置")
    return value


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """
    格式化时间戳

    Args:
        dt: datetime对象

    Returns:
        格式化的时间字符串
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本

    Args:
        text: 原文本
        max_length: 最大长度
        suffix: 后缀

    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def safe_get(dictionary: Dict[str, Any], *keys, default=None):
    """
    安全获取嵌套字典的值

    Args:
        dictionary: 字典
        *keys: 键路径
        default: 默认值

    Returns:
        字典值或默认值
    """
    for key in keys:
        if isinstance(dictionary, dict) and key in dictionary:
            dictionary = dictionary[key]
        else:
            return default
    return dictionary


def calculate_engagement_rate(likes: int, shares: int, views: int) -> float:
    """
    计算互动率

    Args:
        likes: 点赞数
        shares: 分享数
        views: 阅读数

    Returns:
        互动率（百分比）
    """
    if views == 0:
        return 0.0
    return round((likes + shares) / views * 100, 2)


def calculate_rf_score(recency: int, frequency: int, monetary: float) -> Dict[str, Any]:
    """
    计算RFM得分

    Args:
        recency: 最近一次互动距今天数
        frequency: 互动次数
        monetary: 互动价值

    Returns:
        RFM分析结果
    """
    # 简化的RFM评分
    r_score = 5 if recency <= 7 else (3 if recency <= 30 else 1)
    f_score = 5 if frequency >= 10 else (3 if frequency >= 5 else 1)
    m_score = 5 if monetary >= 100 else (3 if monetary >= 50 else 1)

    # 细分
    if r_score >= 4 and f_score >= 4:
        segment = "champions"  # 核心价值用户
    elif r_score >= 4 and f_score >= 2:
        segment = "loyal"  # 忠诚用户
    elif r_score >= 3 and f_score >= 3:
        segment = "potential"  # 潜力用户
    elif r_score <= 2 and f_score <= 2:
        segment = "hibernating"  # 休眠用户
    else:
        segment = "price_sensitive"  # 价格敏感

    return {
        "r_score": r_score,
        "f_score": f_score,
        "m_score": m_score,
        "segment": segment
    }


class Timer:
    """计时器"""

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def start(self):
        """开始计时"""
        self.start_time = datetime.now()
        return self

    def stop(self):
        """停止计时"""
        self.end_time = datetime.now()
        return self

    def elapsed(self) -> float:
        """获取耗时（秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def elapsed_ms(self) -> int:
        """获取耗时（毫秒）"""
        return int(self.elapsed() * 1000)
