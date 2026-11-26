"""本機示範目標站：登入 + 分頁商品表 + 市場新聞。
每次成功登入 TICK+1 → 價格微幅變動，供漲跌分析示範。"""
import math
from flask import Flask, request, session, redirect, render_template_string

app = Flask(__name__)
app.secret_key = "demo-secret-key"
TICK = 0
PER_PAGE = 8

BASE = [
    ("無線路由器 X100", "3C家電", 400), ("智慧手環 S2", "3C家電", 250),
    ("藍牙耳機 Air3", "3C家電", 220), ("行動電源 P20", "3C家電", 130),
    ("網路攝影機 C1", "3C家電", 390), ("智慧音箱 M5", "3C家電", 300),
    ("平板電腦 Tab8", "3C家電", 2100), ("電競滑鼠 G7", "3C家電", 310),
    ("雷射印表機 L300", "辦公設備", 1100), ("多功能事務機 M900", "辦公設備", 3000),
    ("碎紙機 SH8", "辦公設備", 480), ("投影機 PJ2", "辦公設備", 3500),
    ("辦公椅 EC5", "辦公設備", 1100), ("升降桌 SD1", "辦公設備", 2210),
    ("白板 WB6", "辦公設備", 450), ("文件櫃 FC3", "辦公設備", 990),
    ("USB-C 集線器 H7", "周邊配件", 150), ("機械鍵盤 K85", "周邊配件", 420),
    ("27吋螢幕 V27", "周邊配件", 890), ("SSD 1TB", "周邊配件", 890),
    ("無線充電盤 W2", "周邊配件", 110), ("筆電支架 LS1", "周邊配件", 160),
    ("視訊鏡頭 WC2", "周邊配件", 300), ("延長線 PB6", "周邊配件", 105),
]

ARTICLES = [
    {"id": 1, "title": "對手 A 調降智慧手環售價 搶攻年終商機", "date": "2026-11-08",
     "content": "對手 A 宣布智慧手環 S2 系列調降售價約 5%，並搭配通路回饋搶攻年終採購商機。"
                "市場預期將帶動整體穿戴裝置價格競爭，中小型品牌恐跟進降價。"},
    {"id": 2, "title": "辦公設備需求回升 企業採購預算增加", "date": "2026-11-06",
     "content": "隨企業年度預算編列完成，辦公設備採購需求回升，印表機與事務機詢問度增加約 12%。"
                "供應商表示交期維持 2-3 週，價格暫無明顯調整。"},
    {"id": 3, "title": "3C 周邊配件供應鏈成本上揚", "date": "2026-11-04",
     "content": "受上游零組件與運費成本上揚影響，3C 周邊配件進貨成本增加 3-6%。"
                "通路業者評估部分品項將於下一季反映售價，建議提前備貨。"},
    {"id": 4, "title": "電商通路周年慶 帶動整體市場買氣", "date": "2026-11-02",
     "content": "主要電商通路周年慶開跑，整體 3C 與辦公用品買氣較上月成長約 15%。"
                "促銷集中在耳機、螢幕與儲存裝置，價格戰預期延續至 11 月底。"},
]

LOGIN_HTML = """<h1>Competitor Portal Login</h1>
<form method="post">
<input name="username" placeholder="username">
<input name="password" type="password" placeholder="password">
<button type="submit">Login</button></form>"""

PRODUCTS_HTML = """<h1>Competitor Products（page {{ page }}）</h1>
<table id="products">
<thead><tr><th>Name</th><th>Category</th><th>Price</th><th>Stock</th><th>URL</th></tr></thead>
<tbody>
{% for p in rows %}<tr><td>{{ p.name }}</td><td>{{ p.category }}</td><td>{{ p.price }}</td>
<td>{{ p.stock }}</td><td>{{ p.url }}</td></tr>{% endfor %}
</tbody></table>
{% if next_page %}<a class="next" href="{{ next_page }}">Next</a>{% endif %}"""

NEWS_HTML = """<h1>Market News</h1>
{% for a in articles %}<article><h2>{{ a.title }}</h2><time>{{ a.date }}</time>
<div class="content">{{ a.content }}</div><a href="/news/{{ a.id }}">link</a></article>{% endfor %}"""


@app.route("/")
def index():
    return redirect("/products")


@app.route("/login", methods=["GET", "POST"])
def login():
    global TICK
    if request.method == "POST":
        if (request.form.get("username"), request.form.get("password")) == ("analyst", "demo123"):
            session["user"] = "analyst"
            TICK += 1
            return redirect("/products")
        return "login failed", 401
    return LOGIN_HTML


@app.route("/products")
def products():
    if "user" not in session:
        return redirect("/login")
    page = max(1, int(request.args.get("page", 1)))
    start, end = (page - 1) * PER_PAGE, page * PER_PAGE
    rows = []
    for i in range(start, min(end, len(BASE))):
        name, cat, base = BASE[i]
        price = round(base * (1 + 0.04 * math.sin(TICK + i)), 2)
        rows.append({"name": name, "category": cat,
                     "price": f"HK$ {price:,.2f}",
                     "stock": "有貨" if i % 5 else "缺貨",
                     "url": f"http://127.0.0.1:5000/product/{i+1}"})
    next_page = f"/products?page={page+1}" if end < len(BASE) else None
    return render_template_string(PRODUCTS_HTML, rows=rows, page=page, next_page=next_page)


@app.route("/news")
def news():
    if "user" not in session:
        return redirect("/login")
    return render_template_string(NEWS_HTML, articles=ARTICLES)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
