
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
# /usr/bin/google-chrome-stable --headless --no-sandbox --disable-gpu --remote-debugging-port=9222
# Xvfb :99 -screen 0 1920x1080x16 & export DISPLAY=:99
# 确保使用虚拟显示
os.environ["DISPLAY"] = ":99"

options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--headless=new")  # 无头模式（可选，Xvfb 已提供虚拟显示）
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")

# 显式指定 Chrome 路径（可选）
options.binary_location = "/usr/bin/google-chrome-stable"

driver = webdriver.Chrome(options=options)

try:
    driver.get("https://www.piyao.org.cn/bq/index.htm")
    print("页面标题:", driver.title)
    driver.save_screenshot("screenshot.png")  # 验证截图功能
finally:
    driver.quit()