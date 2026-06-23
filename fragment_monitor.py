#!/usr/bin/env python3
"""
Fragment Gifts Auction Monitor Bot
يراقب مزادات الهدايا على Fragment ويرسل إشعارات فورية عند ظهور هدايا جديدة
"""

import asyncio
import logging
import json
import hashlib
from datetime import datetime
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.constants import ParseMode

# ─────────────────────────────────────────────
#  إعدادات البوت
# ─────────────────────────────────────────────
BOT_TOKEN   = "8753322256:AAHO8fNNcSyCxUg_WYe1y4ezRJ02Yz0GUSM"
ADMIN_ID    = 7471045862
CHECK_EVERY = 5          # ثواني بين كل فحص
FRAGMENT_URL = "https://fragment.com/gifts?sort=listed&filter=auction"

# ─────────────────────────────────────────────
#  إعداد اللوق
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)s │ %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("FragmentMonitor")

# ─────────────────────────────────────────────
#  Headers تحاكي متصفح حقيقي
# ─────────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://fragment.com/",
    "DNT": "1",
}

# ─────────────────────────────────────────────
#  جلب البيانات من Fragment
# ─────────────────────────────────────────────
async def fetch_gifts(client: httpx.AsyncClient) -> list:
    """
    يجلب قائمة الهدايا من Fragment (مرتبة بـ recently listed).
    يرجع list من dicts بها: id, name, price, link, listed_at
    """
    try:
        resp = await client.get(FRAGMENT_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except httpx.HTTPError as e:
        log.warning(f"HTTP error: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    gifts = []

    # Fragment يعرض الهدايا في عناصر <li> داخل قائمة المزادات
    # نحاول أنماط مختلفة لأن الموقع يغيّر structure أحياناً
    items = (
        soup.select("li.tm-row")           # النمط الشائع
        or soup.select("li[data-id]")       # نمط بديل بـ data-id
        or soup.select("div.tm-row")        # بعض الصفحات تستخدم div
        or soup.select("li.js-row")
    )

    if not items:
        # محاولة قراءة JSON مدمج في الصفحة (Fragment أحياناً يضع البيانات هكذا)
        for script in soup.find_all("script", type="application/json"):
            try:
                data = json.loads(script.string or "")
                # استخراج قائمة الهدايا من JSON
                rows = (
                    data.get("gifts")
                    or data.get("items")
                    or data.get("results")
                    or []
                )
                for row in rows:
                    gifts.append(_parse_json_gift(row))
                if gifts:
                    return gifts
            except Exception:
                pass

        # إذا ما لقينا شي → نرجع قائمة فاضية
        log.debug("لم يتم العثور على هدايا في الصفحة")
        return []

    for item in items:
        gift = _parse_html_item(item)
        if gift:
            gifts.append(gift)

    return gifts


def _parse_html_item(item) -> Optional[dict]:
    """يحلّل عنصر HTML واحد ويرجع dict"""
    try:
        # اسم الهدية
        name_el = (
            item.select_one(".tm-title") or
            item.select_one(".table-cell-name") or
            item.select_one("h3") or
            item.select_one("[class*='name']")
        )
        name = name_el.get_text(strip=True) if name_el else "?"

        # السعر
        price_el = (
            item.select_one(".tm-value") or
            item.select_one(".table-cell-number") or
            item.select_one("[class*='price']")
        )
        price = price_el.get_text(strip=True) if price_el else "?"

        # الرابط
        link_el = item.select_one("a[href]")
        link_href = link_el["href"] if link_el else ""
        link = (
            f"https://fragment.com{link_href}"
            if link_href.startswith("/") else link_href
        )

        # وقت الإدراج (إن وُجد)
        time_el = item.select_one("time") or item.select_one("[data-time]")
        listed_at = (
            time_el.get("datetime") or
            time_el.get("data-time") or
            time_el.get_text(strip=True)
            if time_el else ""
        )

        # معرّف فريد
        gift_id = (
            item.get("data-id") or
            item.get("id") or
            hashlib.md5(f"{name}{price}{link}".encode()).hexdigest()[:10]
        )

        return {
            "id": gift_id,
            "name": name,
            "price": price,
            "link": link,
            "listed_at": listed_at,
        }
    except Exception as e:
        log.debug(f"parse error: {e}")
        return None


def _parse_json_gift(row: dict) -> dict:
    """يحلّل هدية من JSON مدمج في الصفحة"""
    name = row.get("name") or row.get("title") or "?"
    price = str(row.get("price") or row.get("bid") or "?")
    slug  = row.get("slug") or row.get("id") or ""
    link  = f"https://fragment.com/gift/{slug}" if slug else ""
    return {
        "id": str(row.get("id") or slug or hashlib.md5(name.encode()).hexdigest()[:10]),
        "name": name,
        "price": price,
        "link": link,
        "listed_at": str(row.get("listed_at") or row.get("date") or ""),
    }


def _escape_html(text: str) -> str:
    """تجنب XSS بـ escape HTML characters"""
    return (text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


# ─────────────────────────────────────────────
#  إرسال إشعار Telegram
# ─────────────────────────────────────────────
async def notify(bot: Bot, gift: dict) -> None:
    """يرسل إشعار Telegram عند ظهور هدية جديدة"""
    listed_at = gift.get("listed_at") or datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    escaped_name = _escape_html(gift["name"])
    escaped_price = _escape_html(gift["price"])
    escaped_link = _escape_html(gift["link"])
    
    msg = (
        "🎁 <b>هدية جديدة على Fragment!</b>\n\n"
        f"📌 <b>الاسم:</b> {escaped_name}\n"
        f"💰 <b>السعر:</b> {escaped_price} TON\n"
        f"🕐 <b>وقت الإدراج:</b> {listed_at}\n"
        f"🔗 <a href='{escaped_link}'>فتح المزاد</a>"
    )
    try:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=msg,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=False,
        )
        log.info(f"✅ أُرسل إشعار: {gift['name']} — {gift['price']} TON")
    except Exception as e:
        log.error(f"❌ فشل إرسال الإشعار: {e}")


# ─────────────────────────────────────────────
#  الحلقة الرئيسية
# ─────────────────────────────────────────────
async def monitor():
    """الحلقة الرئيسية لمراقبة الهدايا"""
    try:
        bot = Bot(token=BOT_TOKEN)
    except Exception as e:
        log.error(f"❌ فشل إنشاء البوت: {e}")
        return

    seen_ids: set = set()
    first_run = True

    # إشعار بدء التشغيل
    try:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "✅ <b>بوت Fragment بدأ يشتغل</b>\n"
                f"🔄 يفحص كل <b>{CHECK_EVERY} ثواني</b>\n"
                f"🔗 {FRAGMENT_URL}"
            ),
            parse_mode=ParseMode.HTML,
        )
        log.info("البوت بدأ — يراقب مزادات الهدايا على Fragment")
    except Exception as e:
        log.error(f"❌ فشل إرسال إشعار البدء: {e}")

    async with httpx.AsyncClient(follow_redirects=True) as client:
        while True:
            try:
                gifts = await fetch_gifts(client)
                log.info(f"الهدايا الموجودة حالياً: {len(gifts)}")

                if first_run:
                    # أول تشغيل: نحفظ الموجود بدون إشعار
                    for g in gifts:
                        seen_ids.add(g["id"])
                    first_run = False
                    log.info(f"أول فحص: حُفظت {len(seen_ids)} هدية موجودة مسبقاً")
                else:
                    # فحوصات لاحقة: نرسل إشعار لأي هدية جديدة
                    for g in gifts:
                        if g["id"] not in seen_ids:
                            seen_ids.add(g["id"])
                            await notify(bot, g)

            except Exception as e:
                log.error(f"خطأ غير متوقع: {e}", exc_info=True)

            await asyncio.sleep(CHECK_EVERY)


# ─────────────────────────────────────────────
#  نقطة الدخول
# ─────────────────────────────────────────────
if __name__ == "__main__":
    asyncio.run(monitor())
