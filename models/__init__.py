# 各モデルをインポート
from .user import User
# 他のモデルがある場合も同様に追加
# from .other_model import OtherModel

# Alembicや他のスクリプトがapp.modelsをインポートするだけで全モデルを認識できるようにする
__all__ = [
    "User"
    # "OtherModel"  # 他のモデルを追加する場合もここに名前を追加
]