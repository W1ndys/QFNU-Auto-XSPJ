# core/xspj_save.py
# 保存打分结果
from utils.logger import log
from core.login import LoginManager
from core.xspj_find import XspjFind
from core.xspj_list import XspjList
from bs4 import BeautifulSoup
import re
import json


class XspjSave(LoginManager):
    def __init__(self, xspj_path: str):
        super().__init__()
        self.url = f"http://zhjw.qfnu.edu.cn{xspj_path}"
        self.save_do_url = f"http://zhjw.qfnu.edu.cn/jsxsd/xspj/xspj_save.do"

        # 定义两种打分策略
        self.scoring_strategies = {
            "scenario_98": {
                "description": "最高得分（98.98分）",
                "grades": ["优", "优", "优", "优", "优", "优", "优", "良", "优", "优"],
            },
            "scenario_89": {
                "description": "90分以下最高分（89.99分）",
                "grades": [
                    "优",
                    "优",
                    "优",
                    "优",
                    "优",
                    "优",
                    "良",
                    "及格",
                    "中",
                    "良",
                ],
            },
        }

    def get_xspj_save_html(self):
        response = self.session.get(self.url)
        return response.text

    def extract_evaluation_payload(
        self, html_content: str, scenario: str = "scenario_98"
    ):
        """
        从评教详情页的HTML中解析数据，并根据指定的打分策略生成请求体。

        Args:
            html_content (str): 评教详情页面的完整HTML文本。
            scenario (str): 打分策略，可选值: "scenario_98", "scenario_89"

        Returns:
            dict[str, str]: POST请求的数据字典。
                如果解析失败，则返回一个包含错误信息的字典。
        """
        # 验证传入的scenario参数
        if scenario not in self.scoring_strategies:
            return {
                "error": f"无效的打分策略: {scenario}。可用策略: {list(self.scoring_strategies.keys())}"
            }

        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # 1. 提取固定的表单参数
            form = soup.find("form", {"id": "Form1"})
            if not form:
                return {"error": "未在HTML中找到ID为 'Form1' 的表单。"}

            static_params = {}
            # 提取所有隐藏input的值
            for input_tag in form.find_all("input", {"type": "hidden"}):  # type: ignore
                name = input_tag.get("name")  # type: ignore
                value = input_tag.get("value", "")  # type: ignore
                if name and name != "pj06xh":  # pj06xh是动态指标，单独处理
                    static_params[name] = value

            # 2. 提取所有动态评教指标及其选项
            evaluation_data = {}
            indicator_order = []  # 保持页面上的指标顺序

            # 查找所有包含评价指标的表格行 (tr)
            indicator_rows = form.select('tr:has(input[name="pj06xh"])')  # type: ignore

            for row in indicator_rows:
                # 获取指标序号
                indicator_input = row.find("input", {"name": "pj06xh"})
                if not indicator_input:
                    continue

                indicator_id = indicator_input["value"]  # type: ignore
                indicator_order.append(indicator_id)
                evaluation_data[indicator_id] = {}

                # 找到包含所有radio按钮的单元格(td)
                options_cell = row.find("td", {"name": "zbtd"})
                if not options_cell:
                    continue

                # 提取每个等级（优、良、中...）的ID和分数
                for radio in options_cell.find_all("input", {"type": "radio"}):  # type: ignore
                    option_id = radio["value"]  # type: ignore
                    # 等级文本和分数在radio按钮后面的文本节点和隐藏input中
                    option_text_node = radio.next_sibling  # type: ignore
                    score_input = radio.find_next_sibling("input", {"type": "hidden"})  # type: ignore

                    if option_text_node and score_input:
                        # 从" 优(10)"中提取"优"
                        grade_match = re.search(r"(\w+)\(", option_text_node.strip())  # type: ignore
                        if grade_match:
                            grade = grade_match.group(1).strip()
                            score = score_input["value"]  # type: ignore
                            evaluation_data[indicator_id][grade] = {
                                "id": option_id,
                                "score": score,
                            }

            if not evaluation_data or not indicator_order:
                return {"error": "未能从HTML中解析出评教指标。"}

            # 3. 根据选定的策略生成请求体
            selected_strategy = self.scoring_strategies[scenario]
            grades = selected_strategy["grades"]

            # 验证打分列表长度
            if len(grades) != len(indicator_order):
                return {
                    "error": f"打分策略 '{scenario}' 的等级列表长度 ({len(grades)}) 与页面指标数量 ({len(indicator_order)}) 不匹配。"
                }

            payload = static_params.copy()
            payload["issubmit"] = "1"  # 0是保存，1是提交

            for i, indicator_id in enumerate(indicator_order):
                selected_grade = grades[i]
                indicator_info = evaluation_data[indicator_id]

                if selected_grade not in indicator_info:
                    return {
                        "error": f"指标 {indicator_id} 没有名为 '{selected_grade}' 的等级。可用等级: {list(indicator_info.keys())}"
                    }

                # a. 添加所选等级的ID
                payload[f"pj0601id_{indicator_id}"] = indicator_info[selected_grade][
                    "id"
                ]

                # b. 添加该指标下所有等级的分数ID（无论是否选中）
                for grade, values in indicator_info.items():
                    score_key = f"pj0601fz_{indicator_id}_{values['id']}"
                    payload[score_key] = values["score"]

            # c. 最后，将所有pj06xh指标序号添加进去
            # 对于重名键 "pj06xh"，我们需要特殊处理
            # 将指标序号列表作为一个字符串数组传递
            payload["pj06xh"] = indicator_order

            return payload

        except Exception as e:
            return {"error": f"处理HTML时发生未知错误: {e}"}

    def save_do(self, payload: dict):
        """
        发送POST请求保存评教数据

        Args:
            payload (dict): 包含评教数据的字典

        Returns:
            str: 服务器响应文本
        """
        response = self.session.post(self.save_do_url, data=payload)
        return response.text
