# 網站資料自動收集與分析平台（MarketIntel Platform）
Ubuntu + Python venv + Selenium + Pandas + 本地 Ollama。
內建本機示範目標站（localhost:5000 by Flask 合規、可重複）；真實網站須遵守 robots.txt 與使用條款。

## 安裝
1. curl -fsSL https://ollama.com/install.sh | sh && ollama pull qwen2.5:1.5b
2. bash scripts/setup_ubuntu.sh && source venv/bin/activate

## 使用
- Terminal 1: python demo_site/app.py
- Terminal 2:
  - python main.py run            # 登入→收集→清洗→分析→AI→Word 報告
  - python main.py run            # 第二次 → 價格漲跌比較
  - python main.py runs
  - python main.py analyze --run 2
  - python main.py report --run 2

## 新增資料來源
於 config.yaml targets 增加一組設定（login/selector/news）；無需改程式。

## 排程（系統管理自動化）
crontab -e → 0 9 * * * cd /path/to/market_intel && venv/bin/python main.py run
