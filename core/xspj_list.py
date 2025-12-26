# core/xspj_list.py
# 根据评价批次ID获取待评价课程列表
from utils.logger import log
from core.login import LoginManager
from core.xspj_find import XspjFind
import json
import re
from bs4 import BeautifulSoup


class XspjList(LoginManager):
    """传入的内容形如?pj0502id=90FC36409E9645E7973F752FCD15D88A&pj01id=&xnxq01id=2024-2025-2"""

    def __init__(self, xspj_path):
        super().__init__()
        self.url = f"http://zhjw.qfnu.edu.cn/jsxsd/xspj/xspj_list.do{xspj_path}"
        self.xspj_path = xspj_path

    def get_xspj_list(self):
        """获取所有页面的评价列表数据"""
        all_data = []
        page_index = 1

        # 获取第一页数据
        response = self.session.post(self.url)
        first_page_data = extract_table_to_json(response.text)

        if isinstance(first_page_data, str):
            first_page_list = json.loads(first_page_data)
        else:
            first_page_list = first_page_data

        # 检查是否有错误
        if isinstance(first_page_list, dict) and "error" in first_page_list:
            log.error(f"获取第一页数据失败: {first_page_list['error']}")
            return json.dumps(first_page_list, ensure_ascii=False, indent=4)

        all_data.extend(first_page_list)
        log.info(f"获取第{page_index}页数据成功，本页{len(first_page_list)}条数据")

        # 解析总页数
        total_pages = self._extract_total_pages(response.text)
        log.info(f"检测到总共{total_pages}页数据")

        # 如果有多页，继续获取后续页面
        if total_pages > 1:
            # 解析第一页的表单数据，用于后续POST请求
            form_data = self._extract_form_data(response.text)

            for page_index in range(2, total_pages + 1):
                page_data = self._get_page_data(page_index, form_data)
                if page_data:
                    all_data.extend(page_data)
                    log.info(
                        f"获取第{page_index}页数据成功，本页{len(page_data)}条数据"
                    )
                else:
                    log.warning(f"获取第{page_index}页数据失败")

        log.info(f"获取评价列表成功，总共{len(all_data)}条数据")
        return json.dumps(all_data, indent=4, ensure_ascii=False)

    def _extract_total_pages(self, html_content):
        """从HTML中提取总页数"""
        soup = BeautifulSoup(html_content, "lxml")

        # 查找分页信息，通常在页面底部
        # 寻找包含页数信息的元素
        page_info_patterns = [
            r"共(\d+)页",
            r"第\s*\d+\s*/\s*(\d+)\s*页",
            r"页次：\d+/(\d+)",
        ]

        for pattern in page_info_patterns:
            match = re.search(pattern, html_content)
            if match:
                total_pages = int(match.group(1))
                log.debug(f"从页面解析到总页数: {total_pages}")
                return total_pages

        # 如果找不到分页信息，检查是否有"下一页"按钮来判断是否有多页
        next_page_elements = soup.find_all("a", text=re.compile(r"下一页|next", re.I))
        if next_page_elements:
            log.debug("检测到下一页按钮，但无法确定总页数，将逐页获取")
            return self._get_total_pages_by_iteration()

        log.debug("未检测到分页信息，默认为1页")
        return 1

    def _get_total_pages_by_iteration(self):
        """通过逐页尝试来确定总页数"""
        # 这是一个备用方法，当无法直接解析总页数时使用
        # 由于这种方法效率较低，优先使用直接解析的方法
        return 1

    def _extract_form_data(self, html_content):
        """从HTML中提取表单数据"""
        soup = BeautifulSoup(html_content, "lxml")
        form_data = {}

        # 查找所有的input元素
        inputs = soup.find_all("input")
        for input_element in inputs:
            if hasattr(input_element, "get"):
                name = input_element.get("name")  # type: ignore
                value = input_element.get("value", "")  # type: ignore
                if name:
                    # 处理多个同名字段的情况（如多个pj01id）
                    if name in form_data:
                        if not isinstance(form_data[name], list):
                            form_data[name] = [form_data[name]]
                        form_data[name].append(value)
                    else:
                        form_data[name] = value

        # 查找select元素
        selects = soup.find_all("select")
        for select_element in selects:
            if hasattr(select_element, "get"):
                name = select_element.get("name")  # type: ignore
                if name:
                    selected_option = select_element.find("option", {"selected": True})  # type: ignore
                    if selected_option and hasattr(selected_option, "get"):
                        form_data[name] = selected_option.get("value", "")  # type: ignore
                    else:
                        # 如果没有选中的选项，取第一个选项的值
                        first_option = select_element.find("option")  # type: ignore
                        if first_option and hasattr(first_option, "get"):
                            form_data[name] = first_option.get("value", "")  # type: ignore

        log.debug(f"提取到的表单数据: {form_data}")
        return form_data

    def _get_page_data(self, page_index, base_form_data):
        """获取指定页的数据"""
        # 复制基础表单数据
        form_data = base_form_data.copy()
        form_data["pageIndex"] = str(page_index)

        # 处理多值字段（如pj01id）
        post_data = []
        for key, value in form_data.items():
            if isinstance(value, list):
                for v in value:
                    post_data.append(f"{key}={v}")
            else:
                post_data.append(f"{key}={value}")

        post_data_string = "&".join(post_data)

        try:
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": self.url,
                "Origin": "http://zhjw.qfnu.edu.cn",
            }

            response = self.session.post(
                self.url, data=post_data_string, headers=headers
            )

            page_data_json = extract_table_to_json(response.text)
            if isinstance(page_data_json, str):
                page_data = json.loads(page_data_json)
            else:
                page_data = page_data_json

            # 检查是否有错误
            if isinstance(page_data, dict) and "error" in page_data:
                log.error(f"获取第{page_index}页数据失败: {page_data['error']}")
                return None

            return page_data

        except Exception as e:
            log.error(f"获取第{page_index}页数据时发生异常: {str(e)}")
            return None


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
                # 特殊处理"操作"列，提取链接和文本
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
    log.debug(f"提取表格信息成功，返回结果: {all_rows_data}")
    log.info("提取表格信息成功")
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
