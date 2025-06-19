# QFNU-Auto-XSPJ

曲阜师范大学、强智教务 2017 ，自动化一键学生评价、学生评教

## 特色功能

- 🌐 不依赖浏览器，使用 requests 库模拟登录，支持 Windows、Linux、Mac 多系统，就算是一块主板也能用哦！
- ⚡ 无需渲染页面，速度快的起飞，20 门评教 20 秒搞定！
- 📝 支持自动提交文字评价，默认是 A，可以手动修改
- 🎯 自动计算 90 分以上课程，可选指定课程提交
- 📊 高分课程默认 98.98 分，其余课程默认 89.99 分
- 🔑 输入账号密码即可使用，无需手动操作
- 📝 自带日志记录，方便查看运行情况
- 🔍 **支持突破教务限制覆盖提交，可以挽救不小心给老师打低分但无法修改的情况哦！**

## 环境依赖

- Python 3.10-3.12
- 不能超过 3.12，作者只在 3.12 下测试过，其他版本未测试

## 使用方法

### 环境配置

1. 创建虚拟环境

```bash
python -m venv venv
```

2. 激活虚拟环境

在 Windows 下

```cmd
venv\Scripts\activate.bat
```

在 Linux 下

```bash
source venv/bin/activate
```

3. 安装依赖

```bash
pip install -r requirements.txt
```

4. 配置环境变量

```bash
cp .env.example .env
```

5. 运行脚本

```bash
python main.py
```
