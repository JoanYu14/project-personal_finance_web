from datetime import date  # 從 datetime 模組導入 date 類型
from flask_sqlalchemy import SQLAlchemy  # 從 flask_sqlalchemy 導入 SQLAlchemy
from sqlalchemy import Date  # 導入日期型別
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)  # 導入 Mapped 和 mapped_column，用於欄位映射
from typing import Optional  # 導入 Optional，用於定義可選的類型

db = SQLAlchemy()  # 初始化 SQLAlchemy 實例


# 定義 Cash 類別，對應到資料庫中的 Cash 資料表
class Cash(db.Model):  # 繼承自 db.Model，表示這是 Flask-SQLAlchemy 的模型類別
    __tablename__ = "cash"  # 資料表名稱設定為 "cash"

    # 定義資料表欄位
    transaction_id: Mapped[int] = mapped_column(
        db.Integer, primary_key=True, unique=True, autoincrement=True
    )
    taiwanese_dollars: Mapped[int] = mapped_column(
        db.Integer,
    )
    us_dollars: Mapped[float] = mapped_column(
        db.REAL,
    )
    note: Mapped[str] = mapped_column(db.String(30))
    date_info: Mapped[date] = mapped_column(db.Date)  # 生日欄位，使用日期型別

    def __init__(
        self,
        taiwanese_dollars: int = 0,  # 台幣，預設值為 0
        us_dollars: float = 0,  # 美金，預設值為 0
        note: str = "",  # 備註欄
        date_info: date = date.today(),  # 日期欄，預設為當天日期
    ) -> None:
        # 初始化方法，用於創建 Cash 物件
        self.note = note
        self.taiwanese_dollars = taiwanese_dollars
        self.us_dollars = us_dollars
        self.date_info = date_info

    def __repr__(self) -> str:
        # 定義物件的字串表示形式，便於調試和顯示
        return f"<Cash(transaction_id={self.transaction_id}, taiwanese_dollars={self.taiwanese_dollars}, us_dollars={self.us_dollars}, date_info={self.date_info}, note={self.note})>"
