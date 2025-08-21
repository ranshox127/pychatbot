# wsgi.py
from main import create_app
app = create_app()

# app.run(host="0.0.0.0", port=PROD_PORT, ssl_context=('/etc/letsencrypt/live/chatbot.moocs.tw/fullchain.pem', '/etc/letsencrypt/live/chatbot.moocs.tw/privkey.pem'))
"""
你沒有誤會～重點有兩個：

1. **Production 不應直接 `app.run(..., ssl_context=...)`**
   正式環境建議：**Gunicorn（或 uWSGI）在本機跑 HTTP**，**Nginx 終止 SSL** 並反向代理到 Gunicorn。
   這樣穩定、可熱更新、性能與安全性都更好。

2. **Webhook 應在部署流程（或一次性 CLI）設定到固定網域**
   有了固定網域（`https://chatbot.moocs.tw`），用 **CLI 或 CI/CD 步驟**呼叫 LINE 的 `set_webhook_endpoint`，把 URL 設為 `https://chatbot.moocs.tw/<你的 webhook path>`。這一步與應用啟動解耦，成功率高、可重試。

下面給你一套落地做法（最小變更），以及要注意的細節。

---

## A. 正式啟動流程（建議架構）

### 1) WSGI 入口（你已做）

```python
# wsgi.py
from main import create_app
app = create_app()
```

### 2) 啟動 Gunicorn（不要用 app.run）

常見命令（綁 127.0.0.1:8096，由 Nginx 反代過來）：

```bash
APP_ENV=production FLASK_ENV=production \
gunicorn -w 4 -k gthread -b 127.0.0.1:8096 --timeout 60 --graceful-timeout 30 \
  --log-level info wsgi:app
```

（也可以用 Unix socket：`--bind unix:/run/pychatbot.sock`）

### 3) Nginx（SSL 終止 + 反代）

最小示例（請按你的路徑調整）：

```nginx
server {
  listen 443 ssl http2;
  server_name chatbot.moocs.tw;

  ssl_certificate     /etc/letsencrypt/live/chatbot.moocs.tw/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/chatbot.moocs.tw/privkey.pem;

  # LINE 的 webhook POST 會打到這個 path（見下一節注意事項）
  location / {
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_pass http://127.0.0.1:8096;
  }
}

server {
  listen 80;
  server_name chatbot.moocs.tw;
  return 301 https://$host$request_uri;
}
```

> ✅ SSL 掛在 Nginx；Gunicorn 只跑 HTTP。
> ✅ 之後用 systemd 寫 service，開機自動啟。

---

## B. Webhook 設定（在部署流程中做）

### 1) 你已經有 `set_webhook()`；建議搬到 `cli.py` 並做一個 prod 指令

```python
# cli.py（節錄）
from linebot.v3.messaging import ApiClient, Configuration, MessagingApi, SetWebhookEndpointRequest

def set_webhook(token: str, endpoint: str):
    configuration = Configuration(access_token=token)
    with ApiClient(configuration) as api_client:
        api = MessagingApi(api_client)
        api.set_webhook_endpoint(SetWebhookEndpointRequest(endpoint=endpoint))
    print(f"✅ Webhook set to {endpoint}")

def prod_set_webhook():
    from main import create_app
    app = create_app()
    endpoint = "https://chatbot.moocs.tw/linebot/linebot/"  # ⬅️ 注意正確 path（下一節解釋）
    set_webhook(app.config["LINE_ACCESS_TOKEN"], endpoint)

if __name__ == "__main__":
    prod_set_webhook()
```

> 把這步放在部署 pipeline（或手動）執行一次即可。更新 domain/token 時重跑。

### 2) ⚠️ 重要：Webhook Path 要跟你的 Blueprint 相符

你現在的 Blueprint 是：

* `url_prefix='/linebot'`
* 路由：`@linebot_bp.route('/linebot/', methods=['POST'])`

所以**完整路徑是**：`/linebot/linebot/`
你在 dev 的 `set_webhook(... f"{ngrok_url}/linebot/")` 之前是錯的；
**應改成** `... f"{ngrok_url}/linebot/linebot/"`。
同理，prod 也要設成 `https://chatbot.moocs.tw/linebot/linebot/`。

---

## C. 你的兩個疑慮，逐條回覆

1. **「要不要在 prod 程式裡 set webhook？」**
   不建議。把 webhook 設定成 **部署步驟**（CI/CD 或 `cli.py` 手動指令），比程式啟動時執行更可靠（啟動失敗就不會造成 webhook 亂設）。也方便你在域名/環境切換時明確控制。

2. **「prod 不該用 `app.run(...ssl_context=...)`」**
   對，這是開發用簡易 server 的做法。prod 應 Nginx（SSL）→ Gunicorn（WSGI），像上面 A 節那樣。

---

## D. 最小的操作手冊

* **本機開發（mock LINE，或 E2E 時開真 LINE）**

  ```bash
  # 默認：mock LINE
  APP_ENV=development USE_REAL_LINE=false python cli.py dev

  # 需要 E2E：sandbox token/secret + ngrok + set webhook
  APP_ENV=development USE_REAL_LINE=true DEV_LINE_TOKEN=... DEV_LINE_SECRET=... python cli.py dev
  ```

* **部署（Production）**

  1. 設置環境變數（`PROD_LINE_TOKEN`、`PROD_LINE_SECRET`、DB 等）
  2. 啟 Gunicorn（systemd 管理）
  3. Nginx 代理 HTTPS→Gunicorn
  4. **設定 webhook**（只在初次或異動時）：

     ```bash
     APP_ENV=production FLASK_ENV=production python cli.py  # 執行 prod_set_webhook()
     ```

     （或 CI/CD 內直接呼叫 `set_webhook(PROD_LINE_TOKEN, "https://chatbot.moocs.tw/linebot/linebot/")`）

---

## E. 小加分（可選）

* 在 `Nginx` 的 `/linebot/linebot/` location 加 `client_max_body_size 5m;` 等限制。
* 在 `LINE Developers` 後台允許只有 `https://chatbot.moocs.tw/linebot/linebot/` 的 URL。
* Webhook 驗證工具跑一下（後台的「Verify」）。
* 若有多機，webhook 設定只需對外網域一次（由 Nginx/Load Balancer 分流）。

---

如果你要，我可以幫你寫一份最小的 `systemd` 服務檔（Gunicorn）和對應的 Nginx conf 範例，直接放上去就能跑。
"""