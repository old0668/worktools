import os
import httpx
import logging
import subprocess
import platform

logger = logging.getLogger(__name__)

class Notifier:
    def __init__(self):
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.line_notify_token = os.getenv("LINE_NOTIFY_TOKEN")

    def send_system_notification(self, title, message):
        """Cross-platform system notification."""
        sys_type = platform.system()

        if sys_type == "Darwin":  # macOS
            try:
                clean_message = message.replace('"', '\\"').replace("'", "\\'")
                if len(clean_message) > 100: clean_message = clean_message[:97] + "..."
                script = f'display notification "{clean_message}" with title "{title}"'
                subprocess.run(["osascript", "-e", script])
                return True
            except Exception as e:
                logger.error(f"Error sending macOS notification: {e}")
                return False

        elif sys_type == "Windows":  # Windows
            try:
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                toaster.show_toast(title, message, duration=5, threaded=True)
                return True
            except ImportError:
                logger.warning("win10toast not installed. Skipping Windows notification.")
                return False
            except Exception as e:
                logger.error(f"Error sending Windows notification: {e}")
                return False
        return False

    async def send_telegram(self, message):
        if not self.telegram_bot_token or not self.telegram_chat_id:
            logger.warning("Telegram configuration missing. Skipping Telegram notification.")
            return False

        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    logger.info("Successfully sent message to Telegram.")
                    return True
                else:
                    logger.error(f"Telegram API error: {response.text}")
                    return False
            except Exception as e:
                logger.error(f"Error sending to Telegram: {e}")
                return False

    async def send_line(self, message):
        if not self.line_notify_token:
            logger.warning("LINE Notify configuration missing. Skipping LINE notification.")
            return False

        url = "https://notify-api.line.me/api/notify"
        headers = {
            "Authorization": f"Bearer {self.line_notify_token}"
        }
        payload = {
            "message": message
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, data=payload)
                if response.status_code == 200:
                    logger.info("Successfully sent message to LINE Notify.")
                    return True
                else:
                    logger.error(f"LINE Notify API error: {response.text}")
                    return False
            except Exception as e:
                logger.error(f"Error sending to LINE Notify: {e}")
                return False

    async def notify_all(self, summary):
        # 1. System Notification (macOS or Windows)
        self.send_system_notification("News Aggregator", "新聞摘要已生成！")

        # 2. Prefer Telegram for Markdown support
        if self.telegram_bot_token:
            await self.send_telegram(summary)
        
        # 3. Also send to LINE if token is available
        if self.line_notify_token:
            await self.send_line(summary)
