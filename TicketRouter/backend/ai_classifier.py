import requests
from typing import List

DEEPSEEK_API_KEY = "sk-bbde568f378346bd85e643b5dda38336"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"
CATEGORIES = ["网络问题", "硬件故障", "软件异常", "账号权限", "电力照明", "管道漏水", "门窗家具", "空调暖通", "其他问题"]

SYSTEM_PROMPT = (
    "你是一个 IT 运维分拣员。请阅读以下用户的故障描述，"
    "并只能从【网络问题】、【硬件故障】、【软件异常】、【账号权限】、"
    "【电力照明】、【管道漏水】、【门窗家具】、【空调暖通】、【其他问题】九个选项中输出最符合的一个，"
    "不要输出任何多余的解释性文字。"
)
USER_PROMPT_TEMPLATE = "故障描述：\n{description}\n\n请直接返回一个选项。"


def normalize_category(text: str) -> str:
    cleaned = text.replace("[", "").replace("]", "").replace("【", "").replace("】", "").strip()
    for category in CATEGORIES:
        if category in cleaned:
            return category
    if cleaned in CATEGORIES:
        return cleaned
    return cleaned


def rule_based_classification(description: str) -> str:
    text = description.lower()
    network_keywords = ["网络", "连不上", "断网", "Wi-Fi", "wifi", "路由", "ping", "掉线", "服务器", "访问不了"]
    hardware_keywords = ["硬件", "屏幕", "显示", "蓝屏", "主板", "电源", "风扇", "键盘", "鼠标", "硬盘", "笔记本", "打印机"]
    software_keywords = ["软件", "程序", "系统", "崩溃", "卡顿", "异常", "更新", "安装", "报错", "打不开", "死机"]
    account_keywords = ["账号", "账号", "密码", "权限", "登录", "登录不上", "锁定", "认证"]
    electrical_keywords = ["停电", "灯", "照明", "跳闸", "没电", "电力", "插座", "电路", "电闸", "不亮", "灯泡", "灯管", "断电"]
    plumbing_keywords = ["漏水", "水管", "堵塞", "下水道", "水龙头", "地漏", "浸水", "渗水", "排水", "堵了"]
    furniture_keywords = ["门", "门锁", "门框", "门把手", "窗", "窗户", "窗框", "纱窗", "卷帘", "桌椅", "柜子", "抽屉", "家具", "玻璃"]
    hvac_keywords = ["空调", "制冷", "暖气", "温度", "通风", "出风口", "不冷", "不热", "恒温", "暖通", "换气"]

    score = {category: 0 for category in CATEGORIES}

    for keyword in network_keywords:
        if keyword.lower() in text:
            score["网络问题"] += 1
    for keyword in hardware_keywords:
        if keyword.lower() in text:
            score["硬件故障"] += 1
    for keyword in software_keywords:
        if keyword.lower() in text:
            score["软件异常"] += 1
    for keyword in account_keywords:
        if keyword.lower() in text:
            score["账号权限"] += 1
    for keyword in electrical_keywords:
        if keyword.lower() in text:
            score["电力照明"] += 1
    for keyword in plumbing_keywords:
        if keyword.lower() in text:
            score["管道漏水"] += 1
    for keyword in furniture_keywords:
        if keyword.lower() in text:
            score["门窗家具"] += 1
    for keyword in hvac_keywords:
        if keyword.lower() in text:
            score["空调暖通"] += 1

    winner = max(score, key=score.get)
    if score[winner] == 0:
        return "其他问题"
    return winner


def call_deepseek(description: str) -> str:
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT_TEMPLATE.format(description=description)},
        ],
        "max_tokens": 10,
        "temperature": 0,
    }
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()
    if "choices" not in data or not data["choices"]:
        raise ValueError("DeepSeek 返回结果缺失")
    return data["choices"][0]["message"]["content"].strip()


def classify_description(description: str) -> str:
    rule_result = rule_based_classification(description)
    if rule_result == "其他问题":
        return rule_result
    if DEEPSEEK_API_KEY:
        try:
            raw = call_deepseek(description)
            category = normalize_category(raw)
            if category in CATEGORIES:
                return category
        except Exception:
            pass
    return rule_result


SUGGESTION_SYSTEM_PROMPT = (
    "你是一名经验丰富的 IT 运维工程师。请根据用户提供的故障描述和已确定的分类标签，"
    "给出具体、可操作的处理建议。用中文回答，以分步骤的列表形式输出，"
    "每条建议不超过一句话。控制在 200 字以内，不要输出无关内容。"
)
SUGGESTION_USER_PROMPT_TEMPLATE = (
    "故障分类：{category}\n故障描述：{description}\n\n请给出处理建议："
)


def call_deepseek_suggestion(description: str, category: str) -> str:
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": SUGGESTION_SYSTEM_PROMPT},
            {"role": "user", "content": SUGGESTION_USER_PROMPT_TEMPLATE.format(
                category=category, description=description
            )},
        ],
        "max_tokens": 300,
        "temperature": 0,
    }
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()
    if "choices" not in data or not data["choices"]:
        raise ValueError("DeepSeek 返回结果缺失")
    return data["choices"][0]["message"]["content"].strip()


def rule_based_suggestion(description: str, category: str) -> str:
    suggestions = {
        "网络问题": (
            "1. 检查网线是否插好或 Wi-Fi 是否已连接；"
            "2. 尝试重启路由器或调制解调器；"
            "3. 在命令行运行 ping 命令确认网络连通性；"
            "4. 检查 IP 地址和 DNS 配置是否正确；"
            "5. 若仍无法解决，联系网络管理员排查交换机或防火墙配置。"
        ),
        "硬件故障": (
            "1. 检查设备电源线和适配器是否正常连接；"
            "2. 观察设备指示灯和风扇运转是否正常；"
            "3. 若为笔记本，尝试外接显示器以排除屏幕故障；"
            "4. 检查设备是否存在过热情况，清理通风口；"
            "5. 若为打印机，确认纸张和墨盒状态并尝试重启设备。"
        ),
        "软件异常": (
            "1. 尝试重启相关程序，观察问题是否复现；"
            "2. 检查操作系统和软件是否有待安装的更新；"
            "3. 清理临时文件和缓存，释放磁盘空间；"
            "4. 尝试以安全模式启动排查第三方软件冲突；"
            "5. 若问题持续，记录报错信息并提交至 IT 支持。"
        ),
        "账号权限": (
            "1. 确认输入的用户名和密码是否正确；"
            "2. 尝试通过自助重置密码或联系管理员重置；"
            "3. 检查账号是否因多次登录失败被临时锁定；"
            "4. 确认该账号是否拥有所需资源的访问权限；"
            "5. 若为新员工，确认账号是否已完成开通流程。"
        ),
        "电力照明": (
            "1. 检查配电箱断路器是否跳闸，尝试复位；"
            "2. 确认灯泡或灯管是否烧坏需要更换；"
            "3. 检查墙壁插座是否松动或有无烧焦痕迹；"
            "4. 测试相邻房间是否也断电以判断影响范围；"
            "5. 若为线路故障，联系物业电工上门检修。"
        ),
        "管道漏水": (
            "1. 立即找到漏水源头并关闭就近阀门；"
            "2. 用桶或毛巾接住漏水防止地面浸水；"
            "3. 检查水管接口和密封圈是否老化松动；"
            "4. 通知保洁清理地面积水防止人员滑倒；"
            "5. 联系物业水管工进行管道维修或更换。"
        ),
        "门窗家具": (
            "1. 检查门锁是否卡死或门框变形导致无法开合；"
            "2. 检查合页和拉手等五金件是否松动或脱落；"
            "3. 检查窗户密封条是否老化导致漏风漏雨；"
            "4. 若为家具损坏评估是否可自行维修或需更换；"
            "5. 联系后勤部门安排维修人员上门处理。"
        ),
        "空调暖通": (
            "1. 检查温控面板设置是否正确（模式、温度、风速）；"
            "2. 清洁或更换空调回风口的过滤网；"
            "3. 确认室外机是否正常运行有无异响或结霜；"
            "4. 检查门窗是否关闭严密防止冷气或热气外泄；"
            "5. 若仍无法解决联系暖通维保单位上门检修。"
        ),
        "其他问题": (
            "1. 该工单无法自动归类，请人工确认问题类型；"
            "2. 联系报修人进一步了解详情；"
            "3. 根据实际情况指派对应部门处理；"
            "4. 处理完成后记录实际分类以便后续优化；"
            "5. 如需帮助请联系 IT 服务台协调处理。"
        ),
    }
    return suggestions.get(category, "请联系 IT 支持人员进一步排查。")


def generate_suggestion(description: str, category: str) -> str:
    if DEEPSEEK_API_KEY:
        try:
            return call_deepseek_suggestion(description, category)
        except Exception:
            pass
    return rule_based_suggestion(description, category)
