# utils/logger.py
import os
import logging
import colorlog
import datetime


# 保持为函数形式通常更简洁
def setup_logger():
    """
    配置并返回一个全局的logger实例
    """
    # 确保logs目录存在
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 获取根logger
    logger = logging.getLogger("QFNU-CAS-TOKEN")
    if logger.hasHandlers():  # 防止重复添加handler
        logger.handlers.clear()

    logger.setLevel(logging.DEBUG)

    # 配置文件处理器
    file_handler = logging.FileHandler(
        os.path.join(
            log_dir,
            f'QFNU-CAS-TOKEN_{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.log',
        ),
        encoding="utf-8",
    )
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    # 配置控制台处理器
    console_handler = colorlog.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(levelname)s: %(message)s%(reset)s",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# 创建一个全局实例，方便在其他模块中直接导入使用
log = setup_logger()
