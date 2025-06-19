# core/xspj_find.py
# 获取学生评价批次页面的参数路径
import re
from utils.logger import log
from core.login import LoginManager


class XspjFind(LoginManager):
    def __init__(self):
        super().__init__()
        self.url = "http://zhjw.qfnu.edu.cn/jsxsd/xspj/xspj_find.do"

    def get_xspj_path(self):
        """
        获取学生评价批次页面的参数路径
        """
        response = self.session.get(self.url)
        xspj_path = self.extract_xspj_id(response.text)
        log.debug(f"本次评价批次的参数路径: {xspj_path}")
        log.info("获取评价批次参数路径成功")
        return xspj_path

    def extract_xspj_id(self, response_text):
        """
        从响应文本中提取本次评价批次的ID和相关参数
        """
        # 提取完整的评价URL
        pattern = (
            r'<a href="/jsxsd/xspj/xspj_list.do(.*?)" title="点击进入评价">进入评价</a>'
        )
        match = re.search(pattern, response_text)
        if match:
            return match.group(1)
        else:
            log.error("未找到评价URL")
            return None

    def extract_hidden_params(self, response_text):
        """
        从响应文本中提取隐藏的表单参数
        返回包含pj0502id, pj05id, pj02id, pj01id, pj03id的字典
        """
        params = {}

        # 提取pj0502id
        pj0502id_pattern = (
            r'<input type="hidden" name="pj0502id" id="pj0502id" value="([^"]+)"/>'
        )
        pj0502id_match = re.search(pj0502id_pattern, response_text)
        if pj0502id_match:
            params["pj0502id"] = pj0502id_match.group(1)
            log.debug(f"提取到pj0502id: {params['pj0502id']}")
        else:
            log.error("未找到pj0502id")

        # 提取pj05id
        pj05id_pattern = (
            r'<input type="hidden" name="pj05id" id="pj05id" value="([^"]+)"/>'
        )
        pj05id_match = re.search(pj05id_pattern, response_text)
        if pj05id_match:
            params["pj05id"] = pj05id_match.group(1)
            log.debug(f"提取到pj05id: {params['pj05id']}")
        else:
            log.error("未找到pj05id")

        # 提取pj02id
        pj02id_pattern = (
            r'<input type="hidden" name="pj02id" id="pj02id" value="([^"]+)"/>'
        )
        pj02id_match = re.search(pj02id_pattern, response_text)
        if pj02id_match:
            params["pj02id"] = pj02id_match.group(1)
            log.debug(f"提取到pj02id: {params['pj02id']}")
        else:
            log.error("未找到pj02id")

        # 提取pj01id
        pj01id_pattern = (
            r'<input type="hidden" value="([^"]+)" name="pj01id" id="pj01id"/>'
        )
        pj01id_match = re.search(pj01id_pattern, response_text)
        if pj01id_match:
            params["pj01id"] = pj01id_match.group(1)
            log.debug(f"提取到pj01id: {params['pj01id']}")
        else:
            log.error("未找到pj01id")

        # 提取pj03id
        pj03id_pattern = r'<input type="hidden" name="pj03id" value="([^"]+)"/>'
        pj03id_match = re.search(pj03id_pattern, response_text)
        if pj03id_match:
            params["pj03id"] = pj03id_match.group(1)
            log.debug(f"提取到pj03id: {params['pj03id']}")
        else:
            log.error("未找到pj03id")

        if len(params) == 5:
            log.info("成功提取所有隐藏参数")
        else:
            log.warning(f"只提取到 {len(params)} 个参数，预期为5个")

        return params

    def get_hidden_params(self, xspj_path: str):
        """
        获取评价列表页面的五个隐藏参数：pj0502id, pj05id, pj02id, pj01id, pj03id
        """

        if xspj_path:
            # 构建评价列表页面URL
            list_url = f"http://zhjw.qfnu.edu.cn/jsxsd/xspj/xspj_list.do{xspj_path}"
            log.debug(f"正在访问评价列表页面: {list_url}")

            # 请求评价列表页面
            list_response = self.session.get(list_url)

            # 提取隐藏参数
            hidden_params = self.extract_hidden_params(list_response.text)

            if len(hidden_params) == 5:
                log.info("成功获取所有隐藏参数")
                return hidden_params
            else:
                log.error("未能获取完整的隐藏参数")
                return None
        else:
            log.error("无法获取评价路径，无法继续获取隐藏参数")
            return None


if __name__ == "__main__":
    # 初始登录
    login_manager = LoginManager()
    if not login_manager.simulate_login():
        log.error("程序启动失败，无法完成初始登录。")
        exit(0)
    xspj_find = XspjFind()
    xspj_find.get_xspj_path()
