from core.login import LoginManager
from core.xspj_find import XspjFind
from core.xspj_list import XspjList
from core.xspj_save import XspjSave
from core.toSavepj03wjpj import ToSavepj03wjpj
from utils.logger import log
import json
import re
import time
import math
import subprocess


def print_welcome_info():
    log.info("\n" + "=" * 80)
    log.info("欢迎使用曲阜师范大学自动评教脚本")
    log.info("=" * 80)
    log.info("\n\n")
    log.info("作者: W1ndys （卷卷）")
    log.info("开源地址: https://github.com/W1ndys")
    log.info(
        "曲奇教务是一个第三方教务查询工具，为移动端友好而生，有22级师哥个人维护，支持查课表、成绩、考试安排、选课结果、预选课数据、空闲教室、选课推荐、培养方案.......欢迎使用 官网： https://easy-qfnu.top ， 关注微信公众号【曲奇教务】防止迷路"
    )
    log.info(
        "欢迎加入曲奇教务QQ交流群 1053432087，点击链接加入群聊【曲奇教务Easy-QFNU】：https://qm.qq.com/q/MnYOk4ajaq"
    )
    log.info("=" * 80)
    log.info("\n\n")


if __name__ == "__main__":
    try:
        print_welcome_info()
        # 初始登录
        login_manager = LoginManager()
        if not login_manager.simulate_login():
            log.error("程序启动失败，无法完成初始登录。")
            exit(0)

        # 获取评价批次ID
        xspj_find = XspjFind()
        xspj_path = xspj_find.get_xspj_path()
        if xspj_path:
            hidden_params = xspj_find.get_hidden_params(xspj_path)
        else:
            log.error("无法获取评价路径，无法继续获取隐藏参数")
            exit(0)

        input("按回车开始提交文字评价...")
        if hidden_params:
            log.info("开始提交文字评价")
            time.sleep(1)
            # 先填最下面的文字评价，默认是A
            toSavepj03wjpj = ToSavepj03wjpj(hidden_params)
            toSavepj03wjpj_response = toSavepj03wjpj.save_do()
            # 提取alert内的内容
            alert_content = re.search(r"alert\('(.*)'\)", toSavepj03wjpj_response)
            if alert_content:
                toSavepj03wjpj_response = alert_content.group(1)
            else:
                toSavepj03wjpj_response = "未找到alert内容"
            if "保存成功" in toSavepj03wjpj_response:
                log.info(f"文字评价提交成功，返回结果:{toSavepj03wjpj_response}")
            else:
                log.error(f"文字评价提交失败，返回结果:{toSavepj03wjpj_response}")
            log.info("文字评价提交完成")
        else:
            log.warning(
                "无法获取隐藏参数，最下面的文字评价无法提交，将跳过，请手动提交"
            )

        input("按回车开始获取评价列表...")
        # 获取评价列表
        xspj_list = XspjList(xspj_path)
        xspj_list_json = json.loads(xspj_list.get_xspj_list())
        log.info(f"共有{len(xspj_list_json)}条数据")

        # 限制条件: 评价分数大于等于90, 比例不高于全部评价课程的百分之40
        # 允许大于等于90的个数（向上取整）
        max_90_count = math.ceil(len(xspj_list_json) * 0.4)

        log.info("\n" + "=" * 80)
        log.info("课程评教列表")
        log.info("=" * 80)
        log.info(f"总课程数: {len(xspj_list_json)}")
        log.info(f"允许评价分数≥90的课程数量: {max_90_count} (40%限制)")
        log.info("-" * 80)

        # 为每个课程-老师组合分配序号并显示
        for i, item in enumerate(xspj_list_json, 1):
            log.info(f"{i:2d}. 课程: {item['课程名称']:<20} 老师: {item['授课教师']}")

        log.info("=" * 80)
        log.info(f"请选择 {max_90_count} 个课程使用高分策略(98分)")
        log.info("输入序号，用空格分隔 (例如: 1 3 5 7)")
        log.info("留空则随机选择前几个课程使用高分策略")

        # 获取用户输入
        user_input = input("请输入选择的序号: ").strip()

        # 处理用户选择
        high_score_indices = []
        if user_input:
            try:
                # 解析用户输入的序号
                selected_numbers = [int(x) for x in user_input.split()]
                # 验证序号有效性
                for num in selected_numbers:
                    if 1 <= num <= len(xspj_list_json):
                        high_score_indices.append(num - 1)  # 转换为0基索引
                    else:
                        log.warning(f"序号 {num} 超出范围，已忽略")

                # 检查选择数量是否超限
                if len(high_score_indices) > max_90_count:
                    log.warning(
                        f"选择数量 ({len(high_score_indices)}) 超过限制 ({max_90_count})，只取前 {max_90_count} 个"
                    )
                    high_score_indices = high_score_indices[:max_90_count]
                elif len(high_score_indices) < max_90_count:
                    log.info(
                        f"选择数量 ({len(high_score_indices)}) 少于允许数量 ({max_90_count})"
                    )
                    # 询问是否要自动补充
                    auto_fill = input("是否自动补充剩余名额? (y/n): ").strip().lower()
                    if auto_fill == "y":
                        # 从未选择的课程中补充
                        remaining_indices = [
                            i
                            for i in range(len(xspj_list_json))
                            if i not in high_score_indices
                        ]
                        need_count = max_90_count - len(high_score_indices)
                        high_score_indices.extend(remaining_indices[:need_count])
                        log.info(f"已自动补充 {need_count} 个课程使用高分策略")

            except ValueError:
                log.error("输入格式错误，将使用默认策略（前几个课程使用高分）")
                high_score_indices = list(range(max_90_count))
        else:
            # 用户未输入，默认选择前几个
            high_score_indices = list(range(max_90_count))
            log.info(f"未输入选择，默认对前 {max_90_count} 个课程使用高分策略")

        log.info("\n" + "-" * 80)
        log.info("最终策略分配:")
        log.info("高分策略(98分):")
        for idx in high_score_indices:
            item = xspj_list_json[idx]
            log.info(f"  {idx+1:2d}. {item['课程名称']} - {item['授课教师']}")

        log.info("标准策略(89分):")
        for i, item in enumerate(xspj_list_json):
            if i not in high_score_indices:
                log.info(f"  {i+1:2d}. {item['课程名称']} - {item['授课教师']}")
        log.info("-" * 80)

        # 确认执行
        confirm = input("\n确认执行评教? (y/n): ").strip().lower()
        if confirm != "y":
            log.info("已取消执行")
            exit(0)

        # 开始执行评教
        log.info("\n开始执行自动评教...")

        # 首先对所有课程进行89分预打分以清除限制
        log.info("步骤1: 先用89分策略清除系统限制...")
        for i, item in enumerate(xspj_list_json):
            xspj_save = XspjSave(item["操作"]["href"])
            clear_response = xspj_save.clear_restrictions_with_89()

            # 提取alert内的内容
            alert_content = re.search(r"alert\('(.*)'\)", clear_response)
            if alert_content:
                clear_response_text = alert_content.group(1)
            else:
                clear_response_text = "未找到alert内容"

            if "保存成功" in clear_response_text:
                log.info(
                    f"清除限制成功，序号:{i+1:2d}，课程:{item['课程名称']}，老师:{item['授课教师']}"
                )
            else:
                log.warning(
                    f"清除限制可能失败，序号:{i+1:2d}，课程:{item['课程名称']}，老师:{item['授课教师']}，返回:{clear_response_text}"
                )

        log.info("步骤1完成: 所有课程已用89分策略预打分")
        log.info("\n步骤2: 开始按照选定策略重新打分...")

        for i, item in enumerate(xspj_list_json):
            # 根据是否在高分列表中选择策略
            if i in high_score_indices:
                selected_scenario = "scenario_98"
                strategy_desc = "高分策略(98分)"
            else:
                selected_scenario = "scenario_89"
                strategy_desc = "标准策略(89分)"

            # 保存打分结果
            xspj_save = XspjSave(item["操作"]["href"])
            xspj_save_html = xspj_save.get_xspj_save_html()
            # 传入选择的打分策略
            xspj_save_payload = xspj_save.extract_evaluation_payload(
                xspj_save_html, selected_scenario
            )
            xspj_save_response = xspj_save.save_do(xspj_save_payload)
            # 提取alert内的内容
            alert_content = re.search(r"alert\('(.*)'\)", xspj_save_response)
            if alert_content:
                xspj_save_response = alert_content.group(1)
            else:
                xspj_save_response = "未找到alert内容"
            if "保存成功" in xspj_save_response:
                log.info(
                    f"保存打分结果成功，序号:{i+1:2d}，课程:{item['课程名称']}，老师:{item['授课教师']}，策略:{strategy_desc}，返回结果:{xspj_save_response}"
                )
            else:
                log.error(
                    f"保存打分结果失败，序号:{i+1:2d}，课程:{item['课程名称']}，老师:{item['授课教师']}，策略:{strategy_desc}，返回结果:{xspj_save_response}"
                )

        log.info(f"\n评教完成！共处理 {len(xspj_list_json)} 门课程")
        log.info(f"高分策略: {len(high_score_indices)} 门课程")
        log.info(f"标准策略: {len(xspj_list_json) - len(high_score_indices)} 门课程")

    except KeyboardInterrupt:
        log.info("\n用户主动退出程序 (Ctrl+C)")
    except SystemExit:
        log.info("\n程序正常退出")
    except Exception as e:
        log.error(f"\n程序运行出现异常: {e}")
    finally:
        # 无论如何都打开二维码图片
        try:
            qr_path = "./assets/qrcode.jpg"
            subprocess.run(["start", qr_path], shell=True, check=True)
        except Exception as e:
            log.warning(f"发生异常: {e}")
