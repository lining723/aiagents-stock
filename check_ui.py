from playwright.sync_api import sync_playwright
import os

def check_streamlit_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("正在访问Streamlit应用...")
        page.goto('http://localhost:8503')
        
        print("等待页面加载...")
        page.wait_for_load_state('networkidle')
        
        print("截取屏幕截图...")
        screenshot_path = '/tmp/streamlit_ui_check.png'
        page.screenshot(path=screenshot_path, full_page=True)
        
        print("获取页面内容...")
        content = page.content()
        
        print("检查关键元素...")
        has_title = 'AI Agents Stock' in content or '股票' in content
        has_sidebar = 'sidebar' in content.lower()
        
        print(f"页面包含标题: {has_title}")
        print(f"页面包含侧边栏: {has_sidebar}")
        
        print(f"\n截图已保存至: {screenshot_path}")
        print(f"页面大小: {len(content)} 字符")
        
        if has_title and has_sidebar:
            print("\n✅ 页面成功加载！")
        else:
            print("\n⚠️ 页面可能加载异常，请检查截图")
        
        browser.close()

if __name__ == "__main__":
    check_streamlit_ui()
