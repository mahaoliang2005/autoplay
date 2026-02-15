"""配置加载与管理模块."""

import os
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, field_validator


class CaptureConfig(BaseModel):
    """视频捕获配置."""

    device_index: int = 1
    width: int = 1920
    height: int = 1080
    screenshot_interval: float = 2.0
    max_screenshots: int = 10


class StorageConfig(BaseModel):
    """存储配置."""

    screenshot_dir: str = "~/Downloads/autoplay_screenshots"
    auto_cleanup: bool = True

    @field_validator("screenshot_dir")
    @classmethod
    def expand_home(cls, v: str) -> str:
        """展开用户主目录."""
        return str(Path(v).expanduser())


class VisionConfig(BaseModel):
    """图像处理配置."""

    template_path: str = "./target1.png"
    match_threshold: float = 0.2
    scales_start: float = 1.0
    scales_end: float = 1.5
    scales_steps: int = 5
    red_hsv_lower1: list[int] = Field(default_factory=lambda: [0, 50, 50])
    red_hsv_upper1: list[int] = Field(default_factory=lambda: [10, 255, 255])
    red_hsv_lower2: list[int] = Field(default_factory=lambda: [170, 50, 50])
    red_hsv_upper2: list[int] = Field(default_factory=lambda: [180, 255, 255])


class ArduinoConfig(BaseModel):
    """Arduino通信配置."""

    vid: str = "0x2341"
    pid: str = "0x006D"
    baudrate: int = 9600
    timeout: float = 1.0
    max_retries: int = 3
    retry_delay: float = 0.5

    def get_vid_int(self) -> int:
        """获取整数形式的VID."""
        return int(self.vid, 16)

    def get_pid_int(self) -> int:
        """获取整数形式的PID."""
        return int(self.pid, 16)


class KeyboardConfig(BaseModel):
    """键盘控制配置."""

    exit_key: str = "esc"
    movement_keys: list[str] = Field(default_factory=lambda: ["w", "a", "s", "d"])
    action_keys: list[str] = Field(default_factory=lambda: ["-", "f", "e", "r", "n"])


class LoggingConfig(BaseModel):
    """日志配置."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    format: Literal["colored", "json", "plain"] = "colored"
    file: str | None = None


class Config(BaseModel):
    """应用总配置."""

    capture: CaptureConfig = Field(default_factory=CaptureConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    vision: VisionConfig = Field(default_factory=VisionConfig)
    arduino: ArduinoConfig = Field(default_factory=ArduinoConfig)
    keyboard: KeyboardConfig = Field(default_factory=KeyboardConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def _apply_env_overrides(config: Config) -> Config:
    """应用环境变量覆盖配置.

    环境变量格式: AUTOPLAY__SECTION__KEY=value
    例如: AUTOPLAY__CAPTURE__DEVICE_INDEX=0
    """
    prefix = "AUTOPLAY__"
    config_dict = config.model_dump()

    for env_key, env_value in os.environ.items():
        if not env_key.startswith(prefix):
            continue

        # 解析环境变量路径
        path = env_key[len(prefix) :].lower().split("__")
        current: Any = config_dict

        # 遍历路径到倒数第二层
        for key in path[:-1]:
            if key in current:
                current = current[key]
            else:
                break
        else:
            # 设置最终值
            final_key = path[-1]
            if final_key in current:
                # 尝试转换类型
                original_value = current[final_key]
                if isinstance(original_value, bool):
                    current[final_key] = env_value.lower() in ("true", "1", "yes")
                elif isinstance(original_value, int):
                    current[final_key] = int(env_value)
                elif isinstance(original_value, float):
                    current[final_key] = float(env_value)
                elif isinstance(original_value, list):
                    # 简单列表解析，逗号分隔
                    current[final_key] = [
                        int(x) if x.isdigit() else x for x in env_value.split(",")
                    ]
                else:
                    current[final_key] = env_value

    return Config(**config_dict)


def load_config(config_path: str | Path = "config.yaml") -> Config:
    """加载配置文件.

    Args:
        config_path: 配置文件路径

    Returns:
        Config对象
    """
    config_file = Path(config_path)

    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        config = Config(**data)
    else:
        config = Config()

    # 应用环境变量覆盖
    return _apply_env_overrides(config)
