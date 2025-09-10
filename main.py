# main.py - simple Telegram auto-forwarder (Telethon + StringSession)
import os
import asyncio
import logging
from telethon import TelegramClient, events
from telethon.sessions import StringSession

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ====== Environment variables (set these in Render) ======
# API_ID  (number)
# API_HASH (string)
# SESSION (Telethon string session)
# SOURCE_ID (comma or space separated IDs or @usernames)   e.g. -1001234567890 or @SourceChannel
# TARGET_ID (comma or space separated IDs or @usernames)   e.g. -1009876543210 or @MyGroup
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
SESSION = os.environ.get("SESSION")
RAW_SOURCES = os.environ.get("SOURCE_ID", "")
RAW_TARGETS = os.environ.get("TARGET_ID", "")

if not API_ID or not API_HASH or not SESSION or not RAW_SOURCES or not RAW_TARGETS:
    logging.error("Missing environment variables. Please set API_ID, API_HASH, SESSION, SOURCE_ID, TARGET_ID.")
    raise SystemExit(1)

try:
    API_ID = int(API_ID)
except:
    logging.error("API_ID must be an integer.")
    raise SystemExit(1)

def parse_list(raw):
    items = []
    for p in raw.replace(',', ' ').split():
        p = p.strip()
        if not p:
            continue
        # keep usernames (start with @) as strings, numeric ids as int
        if p.startswith('@'):
            items.append(p)
        else:
            try:
                items.append(int(p))
            except:
                logging.warning("Ignoring invalid id: %s", p)
    return items

SOURCES = parse_list(RAW_SOURCES)
TARGETS = parse_list(RAW_TARGETS)

if not SOURCES or not TARGETS:
    logging.error("No valid SOURCE_ID or TARGET_ID found.")
    raise SystemExit(1)

client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

@client.on(events.NewMessage(chats=SOURCES))
async def forward_handler(event):
    for tgt in TARGETS:
        try:
            # forward preserving original author
            await client.forward_messages(tgt, event.message)
            logging.info("Forwarded msg %s -> %s", getattr(event.message, "id", ""), tgt)
        except Exception as e:
            logging.exception("Failed to forward to %s: %s", tgt, e)

async def main():
    await client.start()
    logging.info("Bot started. Sources: %s Targets: %s", SOURCES, TARGETS)
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Stopped by user")
