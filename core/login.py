# -*- coding: utf-8 -*-
# core/login.py
from PIL import Image
from io import BytesIO
import os
import json
import colorlog
import logging
import datetime
from dotenv import load_dotenv
from utils.session_manager import get_session
from utils.captcha_ocr import get_ocr_res
import time
import base64


# --- 日志配置 (保持不变) ---
def setup_logger():
    """
    配置日志系统
    """
    # 确保logs目录存在
    if not os.path.exists("logs"):
        os.makedirs("logs")

    # 创建logger
    logger = colorlog.getLogger()
    logger.setLevel(logging.DEBUG)

    # 清除可能存在的处理器
    if logger.handlers:
        logger.handlers.clear()

    # 配置文件处理器
    file_handler = logging.FileHandler(
        os.path.join(
            "logs", f'app_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        ),
        encoding="utf-8",
    )
    file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_formatter)

    # 配置控制台处理器
    console_handler = colorlog.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)s: %(message)s%(reset)s",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )
    console_handler.setFormatter(console_formatter)

    # 添加处理器到logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# --- 登录管理类 ---
class LoginManager:
    """
    专门负责处理登录态的类
    """

    def __init__(self):
        """
        初始化LoginManager
        """
        self.logger = setup_logger()
        load_dotenv()
        self.session = get_session()
        self.user_account, self.user_password = self._get_user_config()
        self.base_url = "http://zhjw.qfnu.edu.cn"

    def _get_user_config(self):
        """
        获取用户配置
        返回: (用户账号, 用户密码)
        """
        config_path = "config.json"
        if not os.path.exists(config_path):
            default_config = {"user_account": "", "user_password": ""}
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, ensure_ascii=False, indent=4)
            self.logger.error(
                f"配置文件不存在，已创建默认配置文件 {config_path}\n请填写相关信息后重新运行程序"
            )
            exit(0)

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        required_fields = ["user_account", "user_password"]
        for field in required_fields:
            if not config.get(field):
                raise ValueError(f"配置文件中缺少必填字段: {field}")

        return config["user_account"], config["user_password"]

    def _handle_captcha(self):
        """
        获取并识别验证码
        返回: 识别出的验证码字符串
        """
        rand_code_url = f"{self.base_url}/jsxsd/verifycode.servlet"
        try:
            response = self.session.get(rand_code_url)
            response.raise_for_status()  # 如果请求失败则抛出HTTPError
            image = Image.open(BytesIO(response.content))
            return get_ocr_res(image)
        except Exception as e:
            self.logger.error(f"请求或识别验证码失败: {e}")
            return None

    def _generate_encoded_string(self):
        """
        生成登录所需的encoded字符串
        返回: encoded字符串 (账号base64 + %%% + 密码base64)
        """
        account_b64 = base64.b64encode(self.user_account.encode()).decode()
        password_b64 = base64.b64encode(self.user_password.encode()).decode()
        return f"{account_b64}%%%{password_b64}"

    def _login_request(self, random_code, encoded):
        """
        执行登录POST请求
        返回: 登录响应结果
        """
        login_url = f"{self.base_url}/jsxsd/xk/LoginToXkLdap"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/",
        }
        data = {
            "userAccount": "",
            "userPassword": "",
            "RANDOMCODE": random_code,
            "encoded": encoded,
        }
        return self.session.post(login_url, headers=headers, data=data, timeout=10)

    def simulate_login(self, max_retries=3):
        """
        模拟登录全过程
        参数: max_retries - 最大重试次数
        返回: 是否登录成功
        """
        # 1. 访问教务系统首页，获取必要的cookie
        try:
            response = self.session.get(f"{self.base_url}/jsxsd/")
            response.raise_for_status()
            self.logger.info("成功访问教务系统首页，已获取初始Cookie。")
        except Exception as e:
            self.logger.error(f"无法访问教务系统首页: {e}")
            return False

        # 2. 生成加密字符串
        encoded = self._generate_encoded_string()
        self.logger.info(f"encoded: {encoded}")

        # 3. 循环尝试登录
        for attempt in range(max_retries):
            # 获取验证码
            random_code = self._handle_captcha()
            if not random_code:
                self.logger.warning(
                    f"获取验证码失败，稍后重试... (第 {attempt + 1} 次)"
                )
                time.sleep(1)
                continue
            self.logger.info(f"识别出的验证码: {random_code}")

            try:
                # 发起登录请求
                response = self._login_request(random_code, encoded)
                self.logger.info(f"登录响应状态码: {response.status_code}")

                if response.status_code == 200:
                    if "验证码错误" in response.text:
                        self.logger.warning(
                            f"验证码识别错误，正在重试... (第 {attempt + 1}/{max_retries} 次)"
                        )
                        continue
                    if "密码错误" in response.text:
                        self.logger.error("登录失败：用户名或密码错误！")
                        return False
                    # 登录成功后，通过访问主页最终确认
                    if self.check_login_status():
                        self.logger.info("登录成功!")
                        return True
                    else:
                        # 可能是其他未知错误，例如账号被锁定等
                        self.logger.error("登录请求成功，但无法访问主页，登录失败。")
                        return False

            except Exception as e:
                self.logger.error(f"登录过程中发生异常: {e}")

        self.logger.error(f"尝试 {max_retries} 次后登录失败。")
        return False

    def check_login_status(self):
        """
        通过访问学生主页检查当前会话是否有效
        返回: True (有效) / False (无效)
        """
        try:
            main_page_url = f"{self.base_url}/jsxsd/framework/xsMain.jsp"
            response = self.session.get(main_page_url, timeout=5, allow_redirects=False)
            # 正常登录状态下访问主页是200，如果session失效会被重定向到登录页(302)
            if response.status_code == 200 and "用户登录" not in response.text:
                self.logger.info("会话有效，当前处于登录状态。")
                return True
            else:
                self.logger.warning("会话已失效或被重定向到登录页。")
                return False
        except Exception as e:
            self.logger.error(f"检查登录状态时发生错误: {e}")
            return False


def print_welcome():
    logger = logging.getLogger()
    logger.info(f"\n{'*' * 10} 曲阜师范大学模拟登录脚本 {'*' * 10}\n")
    logger.info("By W1ndys")
    logger.info("https://github.com/W1ndys")
    logger.info("\n")
    logger.info(f"当前时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    """
    主函数，协调整个程序的执行流程
    """
    try:
        login_manager = LoginManager()
        print_welcome()

        # 初始登录
        if not login_manager.simulate_login():
            login_manager.logger.error("程序启动失败，无法完成初始登录。")
            return

        # 登录成功后，可以进入一个循环来执行其他任务
        # 这里用一个简单的循环来演示如何保持和检查登录状态
        while True:
            login_manager.logger.info("主程序正在运行... (每60秒检查一次登录状态)")
            time.sleep(60)
            if not login_manager.check_login_status():
                login_manager.logger.warning("检测到登录已掉线，正在尝试重新登录...")
                if not login_manager.simulate_login():
                    login_manager.logger.error("重新登录失败，程序退出。")
                    break

    except Exception as e:
        logging.getLogger().critical(f"程序发生严重错误: {e}")


if __name__ == "__main__":
    main()
