"""程序入口模块."""

import atexit
import time
from pathlib import Path

import keyboard
import structlog

from autoplay.arduino import ArduinoController
from autoplay.capture import VideoCapture, cleanup_directory
from autoplay.config import load_config
from autoplay.keyboard import KeyStateMachine
from autoplay.logger import configure_logging
from autoplay.vision import TargetDetector


def main() -> int:
    """主程序入口.

    Returns:
        退出码，0表示正常退出
    """
    # 加载配置
    config = load_config("config.yaml")

    # 配置日志
    configure_logging(
        level=config.logging.level,
        format=config.logging.format,
        log_file=config.logging.file,
    )
    logger = structlog.get_logger()
    logger.info("程序启动", version="0.1.0")

    # 创建截图目录
    screenshot_dir = Path(config.storage.screenshot_dir)
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    logger.info("截图目录已准备", path=str(screenshot_dir))

    # 注册退出清理
    if config.storage.auto_cleanup:
        atexit.register(cleanup_directory, screenshot_dir)
        logger.info("已注册退出清理")

    # 初始化组件
    try:
        with VideoCapture(config.capture, config.storage) as capture, \
             ArduinoController(config.arduino) as arduino:

            detector = TargetDetector(config.vision)
            key_sm = KeyStateMachine(
                movement_keys=config.keyboard.movement_keys,
                action_keys=config.keyboard.action_keys,
            )
            frame_num = 1

            logger.info(
                "系统初始化完成",
                device_index=config.capture.device_index,
                template_path=config.vision.template_path,
            )
            logger.info("按 %s 键退出程序", config.keyboard.exit_key)

            while True:
                # 检查退出键
                if keyboard.is_pressed(config.keyboard.exit_key):
                    logger.info("退出键被按下，程序结束")
                    break

                try:
                    # 捕获帧
                    capture.capture_frame(frame_num)

                    # 生成按键
                    key = key_sm.next_key()

                    # 目标检测
                    screenshot_path = screenshot_dir / f"screenshot_{frame_num}.png"
                    result = detector.detect(screenshot_path)

                    if result:
                        # 发送控制指令
                        arduino.send_command(
                            result.direction,
                            result.distance,
                            key,
                        )
                        logger.info(
                            "指令已发送",
                            direction=result.direction,
                            distance=result.distance,
                            key=key,
                            confidence=result.confidence,
                        )
                    else:
                        logger.warning("未检测到目标", frame_num=frame_num)

                    frame_num += 1

                except KeyboardInterrupt:
                    logger.info("收到中断信号，程序结束")
                    break
                except Exception as e:
                    logger.error("运行错误", error=str(e), exc_info=True)
                    # 短暂延迟后继续，避免错误循环
                    time.sleep(1)

    except Exception as e:
        logger.error("初始化失败", error=str(e), exc_info=True)
        return 1

    logger.info("程序正常退出")
    return 0


if __name__ == "__main__":
    exit(main())
