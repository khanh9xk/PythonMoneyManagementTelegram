import requests
import json
import locale
import re
import datetime
from decimal import Decimal
import gspread
from google.oauth2.service_account import Credentials

BOT_TOKEN = "7652933427:AAFA-5_ihJtyjrJDjhf0vliNljGLr24WGy0"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"
global TOTAL
CHAT_ID = 7228604530

# Google Sheets setup
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SERVICE_ACCOUNT_FILE = "./googleSheetKeyKhanh9xkk.json"  # Thay thế bằng tên file credentials của bạn

credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(credentials)
sheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/19h2IvB2T5f2FhEtRkSrlNZ54sU564yqKd95SRxrKv44").sheet1 # Thay thế bằng URL của Google Sheets

def get_updates(offset=None):
    url = API_URL + "getUpdates"
    params = {"offset": offset}
    response = requests.get(url, params=params)
    return response.json()["result"]

def send_message(chat_id, text):
    url = API_URL + "sendMessage"
    params = {"chat_id": chat_id, "text": text}
    requests.post(url, params=params)

def main():
    offset = None
    while True:
        TOTAL = Decimal(sheet.cell(3, 4).value.replace(",", "").replace(".", "").replace(" đồng", ""))
        updates = get_updates(offset)
        for update in updates:
            offset = update["update_id"] + 1
            if "message" in update:
                message = update["message"]
                text = message["text"]
                if text.startswith("/set "):
                    reset_text = text.replace("/set ", "")
                    TOTAL = get_currency(reset_text, TOTAL)
                    send_message(CHAT_ID, f"Còn lại: {format_currency(TOTAL)}")
                else:
                    amount_str = text.split(" ")[0]
                    name = text.replace(amount_str, "")
                    currency_str = get_currency(amount_str, TOTAL)
                    if currency_str is not None:
                        TOTAL += currency_str
                        send_message(CHAT_ID, f"Tổng số tiền còn lại: {format_currency(TOTAL)}\nBấm link sau để kiểm tra: https://docs.google.com/spreadsheets/d/19h2IvB2T5f2FhEtRkSrlNZ54sU564yqKd95SRxrKv44")
                        sheet.insert_row([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), name, format_currency(currency_str), format_currency(TOTAL)], 3)

def validate_currency(input_str):
    pattern = r"^[+-]?\d+(\.\d+)?[k]|[+-]?\d+(\.\d+)?[t][r]$"
    return bool(re.match(pattern, input_str))

def get_currency(input_str, total):
    if validate_currency(input_str) is False:
        send_message(CHAT_ID, f"Lỗi cú pháp\nTổng số tiền còn lại: {format_currency(total)}")
        return None
    else:
        input_lower = input_str.lower()
        if input_lower.endswith("k"):
            return Decimal(input_lower[:-1]) * Decimal(1000)
        elif input_lower.endswith("tr"):
            return Decimal(input_lower[:-2]) * Decimal(1000000)
        else:
            return None

def format_currency(balance):
    try:
        locale.setlocale(locale.LC_ALL, 'vi_VN')  # Đặt locale thành tiếng Việt
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, 'vi') # nếu vi_VN không hoạt động, thử vi
        except locale.Error:
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8') 
    formatter = locale.format_string("%d", int(balance), grouping=True)
    return f"{formatter} đồng"

if __name__ == "__main__":
    main()