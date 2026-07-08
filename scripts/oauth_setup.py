"""一次性工具：用 authorization code grant 換取長期有效的 Shopify Admin API access token。

背景：2026年起 Shopify Dev Dashboard 建立的 custom app 不再直接顯示 shpat_ token，
client_credentials grant 又只能用在 development store（付費正式商店會被擋）。
對已安裝在自己商店的 custom app，官方建議的正規做法是 authorization code grant，
換出來的是長期有效（不會 24 小時過期）的 offline access token。

用法：
    python3 scripts/oauth_setup.py

前置條件（.env 裡要有）：
    SHOPIFY_STORE=xxx.myshopify.com
    SHOPIFY_CLIENT_ID=...
    SHOPIFY_CLIENT_SECRET=...

且 Dev Dashboard 這個 app 的 Access 設定頁，Redirect URLs 要加上：
    http://localhost:8787/callback

執行後會印出一個授權連結，用「商店擁有者」的帳號打開、登入、按 Install/Authorize，
腳本會自動接住 callback、換 token、寫回 .env 的 SHOPIFY_ADMIN_TOKEN。
"""

import os
import secrets
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlencode, urlparse, parse_qs

import httpx
from dotenv import load_dotenv, set_key

load_dotenv()

STORE = os.environ.get("SHOPIFY_STORE", "").strip()
CLIENT_ID = os.environ.get("SHOPIFY_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("SHOPIFY_CLIENT_SECRET", "").strip()
SCOPES = "read_products,write_products,read_inventory,write_inventory,read_locations,read_files,write_files"
# 本機沒對外開放時，用 cloudflared quick tunnel 轉一手：
#   cloudflared tunnel --url http://localhost:8787
# 拿到的 https://xxx.trycloudflare.com 網址填在這裡（記得 Dev Dashboard 的
# Redirect URLs 也要同步改成一樣的網址 + /callback，兩邊要一致）。
PUBLIC_TUNNEL_URL = os.environ.get("OAUTH_TUNNEL_URL", "").strip()
REDIRECT_URI = f"{PUBLIC_TUNNEL_URL}/callback" if PUBLIC_TUNNEL_URL else "http://localhost:8787/callback"
STATE = secrets.token_urlsafe(16)

_result = {}


class CallbackHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # 安靜一點，不要洗畫面

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return

        params = parse_qs(parsed.query)
        code = params.get("code", [None])[0]
        state = params.get("state", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

        if state != STATE:
            self.wfile.write("<h1>state 不符，拒絕，請重新執行腳本</h1>".encode("utf-8"))
            _result["error"] = "state mismatch"
        elif not code:
            self.wfile.write("<h1>沒有拿到 code，授權可能被拒絕</h1>".encode("utf-8"))
            _result["error"] = "no code"
        else:
            self.wfile.write("<h1>授權成功，回到終端機看結果，這個分頁可以關掉了</h1>".encode("utf-8"))
            _result["code"] = code


def main():
    if not STORE:
        sys.exit("❌ .env 裡的 SHOPIFY_STORE 是空的，先填商店網域（例如 xxx.myshopify.com）")
    if not CLIENT_ID or not CLIENT_SECRET:
        sys.exit("❌ .env 裡缺 SHOPIFY_CLIENT_ID 或 SHOPIFY_CLIENT_SECRET")

    authorize_url = f"https://{STORE}/admin/oauth/authorize?" + urlencode({
        "client_id": CLIENT_ID,
        "scope": SCOPES,
        "redirect_uri": REDIRECT_URI,
        "state": STATE,
    })

    print("\n請用「商店擁有者」的帳號打開下面這個連結，登入後按 Install/授權：\n")
    print(f"  {authorize_url}\n")
    print("等待授權中（腳本會自動接住 callback）...\n")

    try:
        webbrowser.open(authorize_url)
    except Exception:
        pass

    server = HTTPServer(("localhost", 8787), CallbackHandler)
    while not _result:
        server.handle_request()

    if _result.get("error"):
        sys.exit(f"❌ 授權失敗：{_result['error']}")

    code = _result["code"]

    resp = httpx.post(
        f"https://{STORE}/admin/oauth/access_token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
        },
        timeout=30,
    )
    resp.raise_for_status()
    body = resp.json()
    access_token = body.get("access_token")

    if not access_token:
        sys.exit(f"❌ 沒有拿到 access_token，回應內容：{body}")

    set_key(".env", "SHOPIFY_ADMIN_TOKEN", access_token)
    print("✅ 成功！SHOPIFY_ADMIN_TOKEN 已經寫進 .env")
    print(f"   授權範圍：{body.get('scope', '未知')}")
    print("\n現在可以跑：python3 scripts/push.py products/<product-dir>\n")


if __name__ == "__main__":
    main()
