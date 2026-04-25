import os
from dotenv import load_dotenv

# 加载环境变量（override=True 强制覆盖已存在的环境变量）
load_dotenv(override=True)

# DeepSeek API配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

# 默认AI模型名称（支持任何OpenAI兼容的模型）
DEFAULT_MODEL_NAME = os.getenv("DEFAULT_MODEL_NAME", "deepseek-chat")

# 其他配置
TUSHARE_TOKEN = os.getenv("TUSHARE_TOKEN", "")

# 股票数据源配置
DEFAULT_PERIOD = "1y"  # 默认获取1年数据
DEFAULT_INTERVAL = "1d"  # 默认日线数据

# MiniQMT量化交易配置
MINIQMT_ENABLED = os.getenv("MINIQMT_ENABLED", "false").lower() == "true"
MINIQMT_ACCOUNT_ID = os.getenv("MINIQMT_ACCOUNT_ID", "")
MINIQMT_HOST = os.getenv("MINIQMT_HOST", "127.0.0.1")
MINIQMT_PORT = int(os.getenv("MINIQMT_PORT", "58610"))

MINIQMT_CONFIG = {
    'enabled': MINIQMT_ENABLED,
    'account_id': MINIQMT_ACCOUNT_ID,
    'host': MINIQMT_HOST,
    'port': MINIQMT_PORT,
}

# 邮件通知配置
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.163.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
EMAIL_FROM = os.getenv("EMAIL_FROM", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_TO = os.getenv("EMAIL_TO", "")

# Webhook通知配置
WEBHOOK_ENABLED = os.getenv("WEBHOOK_ENABLED", "false").lower() == "true"
WEBHOOK_TYPE = os.getenv("WEBHOOK_TYPE", "dingtalk")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
WEBHOOK_KEYWORD = os.getenv("WEBHOOK_KEYWORD", "")

# 时区配置
TZ = os.getenv("TZ", "Asia/Shanghai")

# TDX股票数据API配置（源码已迁移至本项目 tdx-api/ 目录）
TDX_ENABLED = os.getenv("TDX_ENABLED", "false").lower() == "true"
TDX_BASE_URL = os.getenv("TDX_BASE_URL", "http://127.0.0.1:8080")

TDX_CONFIG = {
    'enabled': TDX_ENABLED,
    'base_url': TDX_BASE_URL,
}

# 低价擒牛策略监控配置
LOW_PRICE_BULL_SCAN_INTERVAL = int(os.getenv("LOW_PRICE_BULL_SCAN_INTERVAL", "60"))
LOW_PRICE_BULL_HOLDING_DAYS = int(os.getenv("LOW_PRICE_BULL_HOLDING_DAYS", "5"))
