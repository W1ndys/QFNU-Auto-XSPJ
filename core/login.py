# -*- coding: utf-8 -*-
# core/login.py
import os
import logging
import datetime
from dotenv import load_dotenv
from utils.session_manager import get_session
import time
import base64
import requests
import subprocess
from utils.logger import log


# --- 登录管理类 ---
class LoginManager:
    """
    专门负责处理登录态的类
    """

    def __init__(self):
        """
        初始化LoginManager
        """
        load_dotenv()
        self.session = get_session()
        self.user_account, self.user_password = self._get_user_config()
        self.base_url = "http://zhjw.qfnu.edu.cn"

    def _get_user_config(self):
        """
        获取用户配置
        返回: (用户账号, 用户密码)
        """
        # 尝试从环境变量获取
        account = os.getenv("USER_ACCOUNT")
        password = os.getenv("USER_PASSWORD")

        if account and password:
            log.info(f"获取用户配置成功: {account}")
            return account, password

        log.warning("未找到账号密码配置，请手动输入")
        print("请输入教务系统账号和密码:")
        account = input("账号: ").strip()
        password = input("密码: ").strip()

        # 将输入的账号密码保存到环境变量中，避免后续重复输入
        os.environ["USER_ACCOUNT"] = account
        os.environ["USER_PASSWORD"] = password

        return account, password

    def _handle_captcha(self):
        """
        获取并识别验证码
        优先尝试OCR服务器，失败则转为手动输入
        返回: 识别出的验证码字符串
        """
        rand_code_url = f"{self.base_url}/jsxsd/verifycode.servlet"
        try:
            response = self.session.get(rand_code_url)
            response.raise_for_status()  # 如果请求失败则抛出HTTPError
            image_content = response.content

            # 1. 优先尝试OCR服务器
            try:
                ocr_server_url = "http://127.0.0.1:9898/ocr"
                # 准备文件上传
                files = {"file": ("captcha.jpg", image_content, "image/jpeg")}
                # 设置短超时，避免阻塞太久
                ocr_resp = requests.post(ocr_server_url, files=files, timeout=2)

                if ocr_resp.status_code == 200:
                    res_json = ocr_resp.json()
                    if "result" in res_json:
                        ocr_result = res_json["result"]
                        log.info(f"OCR服务器识别成功: {ocr_result}")
                        return ocr_result
            except Exception as e:
                log.warning(f"OCR服务器连接失败或识别出错: {e}，转为手动输入模式")

            # 2. 失败则转为手动输入
            log.info("正在转入手动输入验证码模式...")
            captcha_path = "captcha.jpg"

            # 保存图片到本地
            with open(captcha_path, "wb") as f:
                f.write(image_content)

            # 打开图片 (Windows)
            try:
                if os.name == "nt":
                    os.startfile(captcha_path)
                else:
                    # 对于非Windows系统，尝试使用subprocess调用默认查看器
                    subprocess.run(["xdg-open", captcha_path], check=False)
            except Exception as e:
                log.warning(f"自动打开图片失败，请手动查看目录下 {captcha_path}: {e}")

            # 获取用户输入
            user_input = input("请输入验证码(查看弹出的图片): ").strip()
            return user_input

        except Exception as e:
            log.error(f"获取验证码失败: {e}")
            return None

    def _generate_encoded_string(self):
        """
        生成登录所需的encoded字符串
        返回: encoded字符串 (账号base64 + %%% + 密码base64)
        """
        if not self.user_account or not self.user_password:
            log.error("用户名或密码为空，请检查 .env 文件")
            return None
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
            log.info("成功访问教务系统首页，已获取初始Cookie。")
        except Exception as e:
            log.error(f"无法访问教务系统首页: {e}")
            return False

        # 2. 生成加密字符串
        encoded = self._generate_encoded_string()
        log.debug(f"encoded: {encoded}")

        # 3. 循环尝试登录
        for attempt in range(max_retries):
            # 获取验证码
            random_code = self._handle_captcha()
            if not random_code:
                log.warning(f"获取验证码失败，稍后重试... (第 {attempt + 1} 次)")
                time.sleep(1)
                continue
            log.debug(f"识别出的验证码: {random_code}")

            try:
                # 发起登录请求
                response = self._login_request(random_code, encoded)
                log.debug(f"登录响应状态码: {response.status_code}")

                if response.status_code == 200:
                    if "验证码错误" in response.text:
                        log.warning(
                            f"验证码识别错误，正在重试... (第 {attempt + 1}/{max_retries} 次)"
                        )
                        continue
                    if "密码错误" in response.text:
                        log.error("登录失败：用户名或密码错误！")
                        return False
                    # 登录成功后，通过访问主页最终确认
                    if self.check_login_status():
                        log.debug("登录成功!")
                        return True
                    else:
                        # 可能是其他未知错误，例如账号被锁定等
                        log.error("登录请求成功，但无法访问主页，登录失败。")
                        return False

            except Exception as e:
                log.error(f"登录过程中发生异常: {e}")

        log.error(f"尝试 {max_retries} 次后登录失败。")
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
                log.info("会话有效，当前处于登录状态。")
                return True
            else:
                log.warning("会话已失效或被重定向到登录页。")
                return False
        except Exception as e:
            log.error(f"检查登录状态时发生错误: {e}")
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
            log.error("程序启动失败，无法完成初始登录。")
            return

        # 登录成功后，可以进入一个循环来执行其他任务
        # 这里用一个简单的循环来演示如何保持和检查登录状态
        while True:
            log.info("主程序正在运行... (每60秒检查一次登录状态)")
            time.sleep(60)
            if not login_manager.check_login_status():
                log.warning("检测到登录已掉线，正在尝试重新登录...")
                if not login_manager.simulate_login():
                    log.error("重新登录失败，程序退出。")
                    break

    except Exception as e:
        logging.getLogger().critical(f"程序发生严重错误: {e}")


if __name__ == "__main__":
    main()
