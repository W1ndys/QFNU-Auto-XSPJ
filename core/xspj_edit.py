# core/xspj_edit.py
# 老师的打分页面
from utils.logger import log
from core.login import LoginManager
from core.xspj_find import XspjFind
from core.xspj_list import XspjList
import json


class XspjEdit(LoginManager):
    def __init__(self, xspj_path):
        super().__init__()
        self.url = f"http://zhjw.qfnu.edu.cn{xspj_path}"

    def get_xspj_edit(self):
        log.info(f"访问打分页面: {self.url}")
        response = self.session.get(self.url)
        return response.text


if __name__ == "__main__":
    # 初始登录
    login_manager = LoginManager()
    if not login_manager.simulate_login():
        log.error("程序启动失败，无法完成初始登录。")
        exit(0)

    xspj_find = XspjFind()
    xspj_path = xspj_find.get_xspj_path()
    xspj_list = json.loads(XspjList(xspj_path).get_xspj_list())
    log.info(
        f"获取评价列表成功，共有{len(xspj_list)}条数据,分别有：{[item['授课教师'] for item in xspj_list]}"
    )
    for item in xspj_list:
        xspj_edit = XspjEdit(item["操作"]["href"]).get_xspj_edit()
