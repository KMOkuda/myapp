from __future__ import annotations
import logging
import secrets
import aiofiles
import aiofiles.os as aioos

from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from models.temp_user import TempUser
from models.user import User

from mailer import send_mail

from config import *
from deps import hash_password

from pathlib import Path


logger = logging.getLogger("myapp.registration")

RATE_LIMIT_PER_DAY = 3
MAX_IMAGE_BYTES = 2 * 1024 * 1024  # 2MB

# 仮登録、本登録用のクラス
class RegistrationService:
    def __init__(self, db: Session):
        self.db = db

    # ユーザーを仮登録する
    async def register_temp_user(self, request, name: str, email: str, password: str, profile_image) -> None:
        now = datetime.now(JST)
        # メールアドレス登録済み
        if self._user_email_exists(email):
            raise ValueError("このメールアドレスは既に登録済みです。ログインしてください。")

       # ユーザー名登録済み
        if self._user_name_exists(name):
            raise ValueError("このユーザー名は既に使用されています。別の名前を入力してください。")

        # パスワードの長さチェック
        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValueError("パスワードが短すぎます（8文字以上にしてください）")

        # 画像サイズチェック
        content = await profile_image.read()
        await profile_image.seek(0)
        if len(content) > MAX_IMAGE_BYTES:
            raise ValueError("画像サイズが大きすぎます（2MB以内にしてください）")
        
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
        # 仮登録レコードのidを名前として登録
        try:
            if profile_image is not None:
                await self._save_temp_image(tr.id, profile_image)
        except ValueError as e:
            logger.exception("画像保存で失敗")
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
        suffix = ".jpg"
        if getattr(profile_image, "filename", None):
            fn = profile_image.filename.lower()
            if fn.endswith((".jpg", ".jpeg")):
                suffix = ".jpg"
            elif fn.endswith(".png"):
                suffix = ".png"

        out = TMP_PROFILES_DIR / f"{temp_id}{suffix}"
        content = await profile_image.read()
        await profile_image.seek(0)
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

    # 仮登録から本登録へ
    async def complete_registration(self, token: str) -> None:
        """
        本登録処理：
        - tokenでTempUserを取得
        - 有効期限（2時間）内か検証
        - Usersへ本登録
        - 仮フォルダの画像を本フォルダへ移動（ユーザーIDベースにリネーム）
        - 仮登録レコードと一時画像の掃除
        """
        now = datetime.now(JST)

        # 1) 仮登録の取得
        tr: TempUser | None = self.db.execute(
            select(TempUser).where(TempUser.token == token)
        ).scalar_one_or_none()
        if tr is None:
            raise ValueError("無効なURLです。もう一度やり直してください。")

        # 2) 期限チェック（expires_atを信頼／なければ2時間計算）
        expires_at = tr.expires_at or (tr.created_at + timedelta(hours=2))
        if now > expires_at:
            # 期限切れ時は仮画像を消して仮登録も掃除
            await self._remove_temp_image(tr.id)
            self._safe_delete(tr)
            raise ValueError("有効期限切れです。最初からやり直してください。")

        # 3) 既存ユーザーの重複チェック（emailユニーク想定）
        exists = self.db.execute(
            select(User).where(User.email == tr.email)
        ).scalar_one_or_none()
        if exists:
            # 既に本登録済みなら仮登録は不要なので掃除
            await self._remove_temp_image(tr.id)
            self._safe_delete(tr)
            raise ValueError("このメールアドレスは既に登録済みです。ログインしてください。")

        # 4) UsersへINSERT
        user = User(
            name=tr.name,
            email=tr.email,
            password_hash=tr.password_hash,
            created_at=now,
            updated_at=now,
        )

        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
        except IntegrityError as e:
            self.db.rollback()
            # 競合（ユニーク制約など）
            raise ValueError("ユーザーの作成に失敗しました（重複の可能性）。") from e
        except Exception as e:
            self.db.rollback()
            raise ValueError("ユーザーの作成に失敗しました。") from e

        # 5) 画像の移動（tmp -> 本番）
        try:
            await self._promote_profile_image(tr.id, user.id)
        except Exception:
            # 画像移動だけ失敗してもユーザーは作れているのでログだけ残す
            logger.exception("プロフィール画像の移動に失敗しました（user_id=%s）", user.id)

        # 6) 仮登録レコードの削除
        self._safe_delete(tr)

    # 仮フォルダから本番フォルダへ画像を移動
    async def _promote_profile_image(self, temp_id: int, user_id: int) -> None:
        """
        仮プロフィール画像を本番フォルダに移動。
        対応拡張子: .jpg / .png
        - temp:  TMP_PROFILES_DIR / f"{temp_id}.<ext>"
        - final: PROFILES_DIR    / f"{user_id}.<ext>"
        無ければ何もしない。
        """
        src_jpg = TMP_PROFILES_DIR / f"{temp_id}.jpg"
        src_png = TMP_PROFILES_DIR / f"{temp_id}.png"

        if src_jpg.exists():
            dst = PROFILES_DIR / f"{user_id}.jpg"
            PROFILES_DIR.mkdir(parents=True, exist_ok=True)
            await aioos.replace(str(src_jpg), str(dst))
        elif src_png.exists():
            dst = PROFILES_DIR / f"{user_id}.png"
            PROFILES_DIR.mkdir(parents=True, exist_ok=True)
            await aioos.replace(str(src_png), str(dst))
        else:
            # 画像なしならスルー
            return

    # 仮画像を削除
    async def _remove_temp_image(self, temp_id: int) -> None:
        """仮画像を削除（存在すれば）"""
        for ext in (".jpg", ".png"):
            p = TMP_PROFILES_DIR / f"{temp_id}{ext}"
            try:
                if p.exists():
                    await aioos.remove(str(p))
            except FileNotFoundError:
                pass

    # ユーザー名が存在するか
    def _user_name_exists(self, name: str) -> bool:
        return self.db.execute(
            select(func.count()).select_from(User).where(User.name == name)
        ).scalar_one() > 0

    # メールアドレスが存在するか
    def _user_email_exists(self, email: str) -> bool:
        return self.db.execute(
            select(func.count()).select_from(User).where(User.email == email)
        ).scalar_one() > 0