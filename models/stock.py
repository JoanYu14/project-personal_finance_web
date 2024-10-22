from datetime import date  # 從 datetime 模組導入 date 類型
from flask_sqlalchemy import SQLAlchemy  # 從 flask_sqlalchemy 導入 SQLAlchemy
from sqlalchemy import Date  # 導入日期型別
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)  # 導入 Mapped 和 mapped_column，用於欄位映射
from typing import Optional  # 導入 Optional，用於定義可選的類型

db = SQLAlchemy()  # 初始化 SQLAlchemy 實例


# 定義 Stock 類別，對應到資料庫中的 Stock 資料表
class Stock(db.Model):  # 繼承自 db.Model，表示這是 Flask-SQLAlchemy 的模型類別
    __tablename__ = "stock"  # 資料表名稱設定為 "stock"

    # 定義資料表欄位
    transaction_id: Mapped[int] = mapped_column(
        db.Integer, primary_key=True, unique=True, autoincrement=True
    )
    stock_id: Mapped[str] = mapped_column(db.String(10))

    stock_num: Mapped[int] = mapped_column(
        db.Integer,
    )
    stock_price: Mapped[float] = mapped_column(
        db.REAL,
    )
    processing_fee: Mapped[int] = mapped_column(
        db.Integer,
    )
    tax: Mapped[int] = mapped_column(
        db.Integer,
    )
    date_info: Mapped[date] = mapped_column(db.Date)  # 生日欄位，使用日期型別

    def __init__(
        self,
        stock_id: str,
        stock_num: int,
        stock_price: float,
        processing_fee: int,
        tax: int,
        date_info: date = date.today(),  # 日期欄，預設為當天日期
    ) -> None:
        # 初始化方法，用於創建 Cash 物件
        self.stock_id = stock_id
        self.stock_num = stock_num
        self.stock_price = stock_price
        self.processing_fee = processing_fee
        self.tax = tax
        self.date_info = date_info

    def __repr__(self) -> str:
        # 定義物件的字串表示形式，便於調試和顯示
        return f"<Stock(transaction_id={self.transaction_id}, stock_id={self.stock_id}, stock_num={self.stock_num}, stock_price={self.stock_price}, processing_fee={self.processing_fee}, tax={self.tax}, date_info={self.date_info})>"
