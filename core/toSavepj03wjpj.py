from core.login import LoginManager
from core.xspj_find import XspjFind
from utils.logger import log


# 保存评教
class ToSavepj03wjpj(LoginManager):
    def __init__(self, hidden_params: dict):
        super().__init__()
        self.url = "http://zhjw.qfnu.edu.cn/jsxsd/xspj/toSavepj03wjpj.do"
        self.hidden_params = hidden_params

    def save_do(self):
        payload = self.hidden_params
        payload["jynr"] = "A."
        payload["pageIndex"] = "1"
        response = self.session.post(self.url, data=payload)
        return response.text


if __name__ == "__main__":
    # 初始登录
    login_manager = LoginManager()
    if not login_manager.simulate_login():
        log.error("程序启动失败，无法完成初始登录。")
        exit(0)
    xspj_find = XspjFind()
    xspj_path = xspj_find.get_xspj_path()
    if xspj_path:
        hidden_params = xspj_find.get_hidden_params(xspj_path)
    else:
        log.error("无法获取评价路径，无法继续获取隐藏参数")
        exit(0)
    if hidden_params is None:
        log.error("无法获取隐藏参数")
        exit(0)
    toSavepj03wjpj = ToSavepj03wjpj(hidden_params)
    log.info(toSavepj03wjpj.save_do())
