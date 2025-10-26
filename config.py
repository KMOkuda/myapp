import os
from datetime import timedelta
from zoneinfo import ZoneInfo
from pathlib import Path

# タイムゾーン
JST = ZoneInfo("Asia/Tokyo")

# メディア保存先
MEDIA_ROOT = "/srv/app/media"
TMP_PROFILES_DIR = Path(os.path.join(MEDIA_ROOT, "tmp/profiles"))
PROFILES_DIR = os.path.join(MEDIA_ROOT, "profiles")

# 制限値
MAX_FILE_SIZE = 2 * 1024 * 1024            # 2MB
TOKEN_TTL = timedelta(hours=2)              # 仮登録の有効期限
DAILY_LIMIT = 3                             # 同一メールの1日上限

# メール
MAIL_FROM_NAME = "myapp"
MAIL_FROM_ADDR = "noreply@test.igovote.net"
SMTP_HOST = "localhost"
SMTP_PORT = 25

# アプリのURL組み立て（Nginxなし）
def absolute_url(request, path: str) -> str:
    proto = request.url.scheme
    host = request.headers.get("host") or request.url.hostname
    return f"{proto}://{host}{path}"