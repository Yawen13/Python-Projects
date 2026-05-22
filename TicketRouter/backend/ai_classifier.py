import requests
from typing import List

# 已直接写入 DeepSeek API Key
DEEPSEEK_API_KEY = "sk-2e2848b5210a49eca40be2342dfddb33"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"
CATEGORIES = ["网络问题", "硬件故障", "软件异常", "账号权限"]

SYSTEM_PROMPT = (
    "你是一个 IT 运维分拣员。请阅读以下用户的故障描述，"
    "并只能从【网络问题】、【硬件故障】、【软件异常】、【账号权限】四个选项中输出最符合的一个，"
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
    hardware_keywords = ["硬件", "屏幕", "显示", "蓝屏", "主板", "电源", "风扇", "键盘", "鼠标", "硬盘", "笔记本", "打印机", "坏了"]
    software_keywords = ["软件", "程序", "系统", "崩溃", "卡顿", "异常", "更新", "安装", "报错", "打不开", "死机"]
    account_keywords = ["账号", "账号", "密码", "权限", "登录", "登录不上", "锁定", "认证"]

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

    winner = max(score, key=score.get)
    if score[winner] == 0:
        return "软件异常"
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
    if DEEPSEEK_API_KEY:
        try:
            raw = call_deepseek(description)
            category = normalize_category(raw)
            if category in CATEGORIES:
                return category
        except Exception:
            pass
    return rule_based_classification(description)
