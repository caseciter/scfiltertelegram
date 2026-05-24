import os
import sys
import requests
from playwright.sync_api import sync_playwright

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
URL = "https://sciter.vercel.app/"

def send_telegram_message(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: Telegram credentials missing.")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("Message sent successfully to Telegram.")
        else:
            print(f"Failed to send message: {response.text}")
    except Exception as e:
        print(f"Error sending to Telegram: {e}")

def scrape_metrics():
    with sync_playwright() as p:
        # Launch headless browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print(f"Navigating to {URL}...")
        page.goto(URL, wait_until="networkidle")
        
        # Give extra time for the automated processing/keyword section to render completely
        page.wait_for_timeout(5000)
        
        # Locate the element based on the layout context
        # We target elements containing or immediately following the "Keyword Match Metrics Summary" header
        try:
            # Locate the heading first
            heading_locator = page.locator("text=Keyword Match Metrics Summary")
            
            if heading_locator.count() == 0:
                print("Could not find the target section header on the page.")
                browser.close()
                return None
                
            # Target the container holding the summary text or table structure
            # Adjusting to capture the text block containing the metric details
            metrics_box = page.locator("div:has-text('Keyword Match Metrics Summary')").last
            
            # Extract text content
            raw_text = metrics_box.text_content()
            
            # Clean up the output to include only the relevant metrics breakdown
            lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
            
            # Reconstruct text beautifully for Telegram
            formatted_text = "<b>📋 KEYWORD MATCH METRICS SUMMARY</b>\n\n"
            
            # Filter out generic header wrapper text if redundant
            record_content = False
            for line in lines:
                if "Keyword Match Metrics Summary" in line:
                    record_content = True
                    continue
                if "Filter View Target" in line:  # Stop before entering UI controls
                    break
                if record_content:
                    formatted_text += f"• {line}\n"
            
            browser.close()
            return formatted_text if record_content else "\n".join(lines)
            
        except Exception as e:
            print(f"Error during extraction: {e}")
            browser.close()
            return None

if __name__ == "__main__":
    metrics_summary = scrape_metrics()
    if metrics_summary:
        print("Extracted content:\n", metrics_summary)
        send_telegram_message(metrics_summary)
    else:
        print("No content extracted.")
