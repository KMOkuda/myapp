from __future__ import annotations
import logging
import secrets
import aiofiles

from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from models.temp_user import TempUser  
from mailer import send_mail

from config import *
from deps import hash_password

logger = logging.getLogger("myapp.registration")

RATE_LIMIT_PER_DAY = 3
MAX_IMAGE_BYTES = 2 * 1024 * 1024  # 2MB


class RegistrationService:
    def __init__(self, db: Session):
        self.db = db

    async def register_temp_user(self, request, name: str, email: str, password: str, profile_image) -> None:
        now = datetime.now(JST)

        # 1) レート制限: 過去24hの同一メールの仮登録件数で判定
        if not self._under_rate_limit(email, now):
            raise ValueError("登録メール送信回数の上限に達しました（1日3回まで）。しばらくしてからお試しください。")

        # 2) 仮登録作成（毎回新規INSERT）
        try:
            tr = self._create_temp_user(name, email, password, now)
        except Exception as e:
            logger.exception("create_temp_user で失敗")
            raise ValueError("仮登録に失敗しました。時間を置いて再度お試しください。") from e

        # 3) 画像保存
        try:
            if profile_image is not None:
                await self._save_temp_image(tr.id, profile_image)
        except ValueError as e:
            if str(e) == "IMAGE_TOO_LARGE":
                # 失敗時は作ったレコードを戻す
                self._safe_delete(tr)
                raise ValueError("画像サイズが大きすぎます（2MB以内にしてください）")
            logger.exception("画像保存で失敗")
            self._safe_delete(tr)
            raise ValueError("画像の保存に失敗しました。時間を置いて再度お試しください。")

        # 4) メール送信
        complete_url = self._build_complete_url(request, tr.token)
        subject = "【囲碁ブック】本登録のご案内"
        body = (
            "仮登録を受け付けました。\n"
            "以下のURLにアクセスして、2時間以内に登録を完了させてください。\n\n"
            f"{complete_url}\n\n"
            "※このメールに心当たりがない場合は破棄してください。"
        )
        try:
            send_mail(email, subject, body)
        except Exception as e:
            logger.exception("メール送信に失敗")
            self._safe_delete(tr)
            raise ValueError("メール送信に失敗しました。時間を置いて再度お試しください。") from e

    # 1日に送れる送信数以内かを返す
    def _under_rate_limit(self, email: str, now: datetime) -> bool:
        since = now - timedelta(days=1)
        count = self.db.execute(
            select(func.count())
            .select_from(TempUser)
            .where(TempUser.email == email, TempUser.created_at >= since)
        ).scalar_one()
        return count < RATE_LIMIT_PER_DAY

    # 仮登録を作成する
    def _create_temp_user(self, name: str, email: str, password: str, now: datetime) -> TempUser:
        token = secrets.token_urlsafe(32)
        password_hash = hash_password(password)

        tr = TempUser(
            name=name,
            email=email,
            password_hash=password_hash,
            token=token,
            created_at=now,
            expires_at=now + timedelta(hours=2),
        )
        self.db.add(tr)
        self.db.commit()
        self.db.refresh(tr)
        return tr

    # 画像を保存する
    async def _save_temp_image(self, temp_id: int, profile_image) -> None:
        content = await profile_image.read()
        if len(content) > MAX_IMAGE_BYTES:
            raise ValueError("IMAGE_TOO_LARGE")

        suffix = ".jpg"
        if getattr(profile_image, "filename", None):
            fn = profile_image.filename.lower()
            if fn.endswith((".jpg", ".jpeg")):
                suffix = ".jpg"
            elif fn.endswith(".png"):
                suffix = ".png"

        out = TMP_PROFILES_DIR / f"{temp_id}{suffix}"
        
        async with aiofiles.open(out, "wb") as f:
            await f.write(content)
        await profile_image.seek(0)  # 戻す

    # 完了URLを組み立てる
    def _build_complete_url(self, request, token: str) -> str:
            return str(request.url_for("complete_user_registration", token=token))

    # 仮登録を削除する
    def _safe_delete(self, obj) -> None:
        try:
            self.db.delete(obj)
            self.db.commit()
        except Exception:
            self.db.rollback()