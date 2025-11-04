FLASH_KEY = "_flash_message"


def set_flash(request, message: str) -> None:
    """
    次のリクエストで1回だけ表示するフラッシュメッセージを設定する
    """
    request.session[FLASH_KEY] = message


def pop_flash(request):
    """
    フラッシュメッセージを取得して、セッションから削除する
    """
    return request.session.pop(FLASH_KEY, None)