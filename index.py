from flask import Flask, render_template, request, redirect  # 從 Flask 導入必要的模組
from flask_sqlalchemy import SQLAlchemy  # 從 Flask-SQLAlchemy 導入 SQLAlchemy 類
from sqlalchemy import func
from collections import namedtuple
import datetime  # 導入 datetime 模組以處理日期
import os
import requests
from models.cash import Cash  # 導入定義在 models/cash.py 裡的 Cash 模型
from models.stock import Stock
import matplotlib.pyplot as plt
import matplotlib
import os

matplotlib.use("agg")  # 使用agg模式以在後端生成圖片


app = Flask(__name__)  # 建立 Flask 應用程式實例
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"sqlite:///{os.path.join(os.getcwd(), 'datafile.db')}"  # 設定 SQLite 資料庫的路徑
)
db = SQLAlchemy(app)  # 初始化 SQLAlchemy，並將 Flask 應用程式與資料庫連結


# 首頁路由，顯示首頁
@app.route("/")
def home():
    # ======== 獲得Cash相關資料 ========

    cash_result = db.session.query(Cash).all()

    # 獲取匯率
    r = requests.get("https://tw.rter.info/capi.php")
    currency = r.json()
    usdtwd_Exrate = currency["USDTWD"]["Exrate"]

    # # 定義Result nametuple
    Result = namedtuple(
        "Result",
        [
            "ntd_sum",
            "usd_sum",
            "usd_sum_to_ntd",
            "usdtwd_exrate",
            "cash_result",
            "stock_result",
            "show_chart1",
            "show_chart2",
        ],
    )

    # 使用sqlAlchemy來query去加總結果
    sum_result = db.session.query(
        func.coalesce(func.sum(Cash.taiwanese_dollars), 0).label("ntd_sum"),
        func.coalesce(func.sum(Cash.us_dollars), 0).label("usd_sum"),
        func.floor(func.coalesce(func.sum(Cash.us_dollars), 0) * usdtwd_Exrate).label(
            "usd_sum_to_ntd_floor"
        ),
        func.cast(usdtwd_Exrate, db.Float).label("usdtwd_exrate"),  # 使用已定義的匯率
    ).first()

    # ======== 獲得Stock相關資料 ========
    all_stock_result = db.session.query(Stock).all()

    # 定義get_stock_info函數，用在map函數中，取得指定股票的當日股價再算出當日市值和報酬率
    def get_stock_info(stock_result):
        # 給API的參數
        param = {"response": "json", "stockNo": stock_result[0]}
        # 取得股價相關資訊
        stock_info = requests.get(
            "https://www.twse.com.tw/exchangeReport/STOCK_DAY", params=param
        )
        data = stock_info.json()["data"]
        # index為最近一天的
        index = len(data) - 1
        # 當前股價
        now_price = float(data[index][6].replace(",", ""))
        # 當前市值
        now_mc = round(stock_result[1] * now_price, 2)
        # 報酬率
        roi = round((now_mc - stock_result[2]) / stock_result[2], 4)

        # 回傳一個dictionary
        return {
            "id": stock_result[0],
            "total_stock_counts": stock_result[1],
            "now_price": now_price,
            "now_mc": now_mc,
            "total_stock_cost": round(stock_result[2]),
            "average_cost": stock_result[3],
            "roi": round(roi * 100, 2),
        }

    # for r in all_stock_result:
    #     print(
    #         f"交易ID:{r.transaction_id}，股票代號:{r.stock_id}，購買股數:{r.stock_num}，購買成本:{r.stock_price}，手續費:{r.processing_fee}，交易稅:{r.tax}"
    #     )

    # 使用sqlAlchemy group_by得到各個股票代號、總股數、總成本、平均成本
    stock_result = (
        db.session.query(
            Stock.stock_id,
            func.sum(Stock.stock_num).label("total_num"),
            func.sum(
                (Stock.stock_num * Stock.stock_price) + Stock.processing_fee + Stock.tax
            ).label("total_price"),
            func.round(
                (
                    func.sum((Stock.stock_num * Stock.stock_price))
                    / func.sum(Stock.stock_num)
                ),
                2,
            ).label("average_price"),
        )
        .group_by(Stock.stock_id)
        .all(),
    )

    # 得到當前股價、當前市值、報酬率
    all_stock_info_result = list(map(get_stock_info, stock_result[0]))

    # print(all_stock_info_result)

    # 算出當前總市值
    total_now_mc = 0
    # 迭代所有股票資訊結果，將每支股票的市值累加到total_now_mc
    for r in all_stock_info_result:
        total_now_mc += r["now_mc"]  # now_mc是每支股票當前市值的 key

    # 使用 map 函數處理股票資訊列表，計算每支股票的市值占比並添加到結果中
    final_stock_info = list(  # 將結果轉換成列表形式
        map(
            # 定義一個 lambda 函數，將每個股票資訊字典中的"now_mc"計算市值占比後，合併到原本的字典中
            lambda x: {
                **x,  # 保留原有的字典資料
                # 計算市值占比，並將結果四捨五入到小數點後兩位
                "mc_percent": round((x["now_mc"] / total_now_mc) * 100, 2),
            },
            all_stock_info_result,  # 傳入所有股票的資訊列表進行處理
        )
    )

    # for i in final_stock_info:
    #     print(i)
    #     print(
    #         f'股票代號:{i["id"]}，持有股數:{i["total_stock_counts"]}，目前股價:{i["now_price"]}，目前市值:{i["now_mc"]}，股票資產占比(%):{i["mc_percent"]}%，購買總成本(包含手續費){i["total_stock_cost"]}，平均成本:{i["average_cost"]}，報酬率:{i["roi"]}%'
    #     )

    # 創建一個Result nametuple
    result_dict = Result(
        *sum_result,
        cash_result=cash_result,
        stock_result=final_stock_info,
        show_chart1=os.path.exists("static/piechart.jpg"),
        show_chart2=os.path.exists("static/piechart2.jpg"),
    )

    # print(
    #     f"台幣總額:{result_dict.ntd_sum}，美金總額:{result_dict.usd_sum}，今日匯率:{result_dict.usdtwd_exrate}，美金換成台幣總額:{result_dict.usd_sum_to_ntd}"
    # )

    # ===== 股票庫存占比圖 =====
    # 如果 final_stock_info 列表中有資料，則繪製圓餅圖
    if len(final_stock_info) > 0:
        # 提取每支股票的 id 作為標籤
        labels = tuple([stock["id"] for stock in final_stock_info])
        # 提取每支股票的市值作為圓餅圖的比例
        sizes = [r["now_mc"] for r in final_stock_info]

        # 創建一個 6x5 英寸的畫布和子圖
        fig, ax = plt.subplots(figsize=(6, 5))

        # 使用市值大小繪製圓餅圖，labels 代表股票代號，autopct=None 表示不顯示百分比，shadow=None 表示不需要陰影
        ax.pie(sizes, labels=labels, autopct=None, shadow=None)

        # 調整圖表的邊距，避免圖形超出範圍
        fig.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)

        # 將圖表儲存為靜態圖像，存放在 "static" 資料夾下，解析度為 200 dpi
        plt.savefig("static/piechart.jpg", dpi=200)
    else:
        # 如果 final_stock_info 沒有資料，嘗試刪除先前生成的圓餅圖
        try:
            os.remove("static/piechart.jpg")
        except:
            pass  # 若刪除失敗則忽略錯誤

    # ===== 股票現金圓餅圖 =====
    if total_now_mc != 0 or result_dict.ntd_sum != 0 or result_dict.usd_sum != 0:
        labels = ("TWD", "USD", "Stock")
        sizes = (
            result_dict.usd_sum * result_dict.usdtwd_exrate,
            result_dict.ntd_sum,
            total_now_mc,
        )
        fig, ax = plt.subplots(figsize=(6, 5))
        ax.pie(sizes, labels=labels, autopct=None, shadow=None)
        fig.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
        plt.savefig("static/piechart2.jpg", dpi=200)
    else:
        try:
            os.remove("static/piechart2.jpg")
        except:
            pass

    return render_template(
        "index.html", data=result_dict
    )  # 渲染 index.html 模板並顯示在首頁


# 顯示 "cash" 表單的路由，使用 GET 方法
@app.route("/cash")
def cash_form():
    return render_template("cash.html")  # 渲染 cash.html 模板顯示 cash 表單


# 提交 "cash" 表單的路由，使用 POST 方法來處理表單數據
@app.route("/cash", methods=["POST"])
def submit_cash():
    taiwanese_dollars = 0
    us_dollars = 0
    note = ""
    submit_date = datetime.date.today().strftime("%Y-%m-%d")
    # 從 POST 請求中取得表單數據
    if request.values["taiwanese-dollars"]:
        taiwanese_dollars = request.values["taiwanese-dollars"]  # 取得台幣欄位值
    if request.values["us-dollars"]:
        us_dollars = request.values["us-dollars"]  # 取得美金欄位值
    if request.values["note"]:
        note = request.values["note"]  # 取得備註欄位值
    if request.values["date"]:
        submit_date = request.values["date"]  # 取得日期欄位值

    # 創建一個新的 Cash 物件（但尚未保存到資料庫）
    new_cash_obj = Cash(
        taiwanese_dollars=int(taiwanese_dollars),
        us_dollars=float(us_dollars),
        note=note,
        date_info=datetime.datetime.strptime(
            submit_date, "%Y-%m-%d"
        ).date(),  # 將日期字串轉換為日期物件
    )

    db.session.add(new_cash_obj)  # 將 Cash 物件添加到資料庫會話
    db.session.commit()  # 提交變更，將數據保存到資料庫

    # 返回表單提交成功訊息，或可導向到其他頁面
    return redirect("/")


@app.route("/cash-delete", methods=["POST"])
def delete_cash_record():
    # 根據 transaction_id 刪除記錄
    want_delete_transaction_id = request.values["id"]
    want_delete_obj = (
        db.session.query(Cash)
        .filter_by(transaction_id=want_delete_transaction_id)
        .first()
    )
    # print(f"要刪除的物件:{ want_delete_obj}")
    db.session.delete(want_delete_obj)
    # 提交變更
    db.session.commit()
    return redirect("/")


# 顯示 "stock" 表單的路由，使用 GET 方法
@app.route("/stock")
def stock_form():
    return render_template("stock.html")  # 渲染 stock.html 模板顯示 stock 表單


@app.route("/stock", methods=["POST"])
def submit_stock():
    tax = 0
    submit_date = datetime.date.today().strftime("%Y-%m-%d")
    processing_fee = 0
    if request.values["tax"]:
        tax = request.values["tax"]
    if request.values["date"]:
        submit_date = request.values["date"]
    if request.values["processing-fee"]:
        processing_fee = request.values["processing-fee"]

    # 以下3項都是必填所以沒有if
    stock_num = request.values["stock-num"]
    stock_price = request.values["stock-price"]
    stock_id = request.values["stock-id"]
    # print(
    #     f"股票代號:{stock_id}，股數:{stock_num}，單價:{stock_price}，手續費:{processing_fee}，交易稅:{tax}，日期:{submit_date}"
    # )
    new_stock_obj = Stock(
        stock_id,
        stock_num,
        stock_price,
        processing_fee,
        tax,
        date_info=datetime.datetime.strptime(
            submit_date, "%Y-%m-%d"
        ).date(),  # 將日期字串轉換為日期物件
    )

    db.session.add(new_stock_obj)  # 將 Cash 物件添加到資料庫會話
    db.session.commit()  # 提交變更，將數據保存到資料庫

    # 返回表單提交成功訊息，或可導向到其他頁面
    return redirect("/")


if __name__ == "__main__":
    # 啟動 Flask 應用程式，並啟用除錯模式
    app.run(debug=True)
