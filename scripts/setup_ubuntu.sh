#!/usr/bin/env bash
set -e
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip fonts-noto-cjk
# Chromium（若套件不存在，請改安裝 Google Chrome .deb，並於 config.yaml 填 binary_path）
sudo apt-get install -y chromium-browser chromium-chromedriver || \
  echo "請安裝 Google Chrome，並設定 browser.binary_path / driver_path"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
mkdir -p data reports logs
python main.py init
echo "完成。請確認：ollama pull qwen2.5:1.5b，並先啟動 python demo_site/app.py"
