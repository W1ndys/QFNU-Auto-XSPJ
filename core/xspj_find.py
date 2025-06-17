# core/xspj_find.py
import re
from utils.logger import log
from core.login import LoginManager


class XspjFind(LoginManager):
    def __init__(self):
        super().__init__()
        self.url = "http://zhjw.qfnu.edu.cn/jsxsd/xspj/xspj_find.do"

    def get_xspj_id(self):
        """
        获取学生评价批次页面
        """
        response = self.session.get(self.url)
        xspj_id = self.extract_xspj_id(response.text)
        log.info(f"本次评价批次的ID: {xspj_id}")

    def extract_xspj_id(self, response_text):
        """
        从响应文本中提取本次评价批次的ID
        """
        # 提取完整的评价URL
        pattern = r'href="(/jsxsd/xspj/xspj_list\.do\?.*?)"'
        match = re.search(pattern, response_text)
        if match:
            return match.group(1)
        else:
            log.error("未找到评价URL")
            return None


if __name__ == "__main__":
    # 初始登录
    login_manager = LoginManager()
    if not login_manager.simulate_login():
        log.error("程序启动失败，无法完成初始登录。")
        exit(0)
    xspj_find = XspjFind()
    xspj_find.get_xspj_id()
