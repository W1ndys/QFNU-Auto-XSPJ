# core/xspj_list.py
# 根据评价批次ID获取待评价课程列表
from utils.logger import log
from core.login import LoginManager
from core.xspj_find import XspjFind
import json
from bs4 import BeautifulSoup


class XspjList(LoginManager):
    """传入的内容形如?pj0502id=90FC36409E9645E7973F752FCD15D88A&pj01id=&xnxq01id=2024-2025-2"""

    def __init__(self, xspj_path):
        super().__init__()
        self.url = f"http://zhjw.qfnu.edu.cn/jsxsd/xspj/xspj_list.do{xspj_path}"

    def get_xspj_list(self):
        response = self.session.get(self.url)
        return extract_table_to_json(response.text)


def extract_table_to_json(html_content):
    """
    从HTML中提取表格信息，并将其整理成JSON格式。

    参数:
    html_content (str): 包含表格的HTML内容的字符串。

    返回:
    str: 包含提取数据的JSON格式字符串。
    """
    # 使用BeautifulSoup和lxml解析器解析HTML
    soup = BeautifulSoup(html_content, "lxml")

    # 查找ID为 "dataList" 的表格
    table = soup.find("table", id="dataList")
    if not table:
        return json.dumps(
            {"error": "未找到ID为'dataList'的表格"}, ensure_ascii=False, indent=4
        )

    # 提取表头 (th)
    headers = [th.get_text(strip=True) for th in table.find_all("th")]  # type: ignore

    # 存储所有行数据的列表
    all_rows_data = []

    # 遍历表格中的所有数据行 (tr)，跳过第一个表头行
    data_rows = table.find_all("tr")[1:]  # type: ignore
    for row in data_rows:
        # 提取当前行的所有单元格 (td)
        cells = row.find_all("td")  # type: ignore
        # 创建一个字典来存储当前行的数据
        row_data = {}
        # 将单元格数据与表头对应起来
        for i, header in enumerate(headers):
            if i < len(cells):
                cell = cells[i]
                # 特殊处理“操作”列，提取链接和文本
                if header == "操作":
                    link = cell.find("a")  # type: ignore
                    if link:
                        row_data[header] = {
                            "text": link.get_text(strip=True),  # type: ignore
                            "href": link.get("href"),  # type: ignore
                        }
                    else:
                        row_data[header] = None
                else:
                    # 对于其他列，直接提取文本内容
                    row_data[header] = cell.get_text(strip=True)
            else:
                row_data[header] = None  # 如果某行单元格数量少于表头，则填充None

        # 将处理完的行数据字典添加到列表中
        all_rows_data.append(row_data)

    # 将数据列表转换为格式化的JSON字符串
    # ensure_ascii=False 确保中文字符能正确显示
    return json.dumps(all_rows_data, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    # 初始登录
    login_manager = LoginManager()
    if not login_manager.simulate_login():
        log.error("程序启动失败，无法完成初始登录。")
        exit(0)
    # 获取评价批次ID
    xspj_find = XspjFind()
    xspj_path = xspj_find.get_xspj_path()
    # 获取评价列表
    xspj_list = XspjList(xspj_path)
    xspj_list_json = json.loads(xspj_list.get_xspj_list())
    log.info(
        f"获取评价列表成功，共有{len(xspj_list_json)}条数据，任课老师有：{[item['授课教师'] for item in xspj_list_json]}"
    )
