#!/usr/bin/env python3
"""
Запусти ОДИН РАЗ после деплоя на Vercel.

Использование:
  python setup_webhook.py <BOT_TOKEN> <VERCEL_URL>

Пример:
  python setup_webhook.py 123456:ABC-xyz https://zevo.vercel.app
"""
import sys, json, urllib.request

if len(sys.argv) < 3:
    print("Использование: python setup_webhook.py BOT_TOKEN VERCEL_URL")
    sys.exit(1)

token = sys.argv[1]
url   = sys.argv[2].rstrip("/") + "/api/webhook"

req = urllib.request.Request(
    f"https://api.telegram.org/bot{token}/setWebhook",
    data=json.dumps({"url": url}).encode(),
    headers={"Content-Type": "application/json"},
)
res = json.loads(urllib.request.urlopen(req).read())
print("✅ Webhook установлен:", url) if res.get("ok") else print("❌ Ошибка:", res)
