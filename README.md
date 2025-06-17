# QFNU-Auto-XSPJ

曲阜师范大学、强智教务自动化学生评价、学生评教

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
