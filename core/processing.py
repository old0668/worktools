import json
import os
import hashlib
import logging
from datetime import datetime, timedelta
from openai import OpenAI
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)
if os.getenv("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY").strip().replace('"', '').replace("'", "")

logger = logging.getLogger(__name__)

class Processor:
    def __init__(self, keywords, config, history_file='data/processed_hashes.json', trend_file='data/sentiment_trends.json', today_news_file='data/today_news.json'):
        self.keywords = keywords
        self.config = config
        self.history_file = history_file
        self.trend_file = trend_file
        self.today_news_file = today_news_file
        self.history = self.load_history()
        self.today_news = self.load_today_news()
        
        # Initialize APIs
        self.openai_client = None
        self.gemini_client = None
        
        gemini_key = os.getenv("GEMINI_API_KEY", "").strip().replace('"', '').replace("'", "")
        openai_key = os.getenv("OPENAI_API_KEY", "").strip().replace('"', '').replace("'", "")
        
        if not gemini_key or gemini_key == "your_gemini_api_key":
            logger.warning("GEMINI_API_KEY is missing or is still a placeholder.")
        else:
            masked_key = f"{gemini_key[:4]}...{gemini_key[-4:]}"
            logger.info(f"Initializing Gemini client with key: {masked_key}")
            try:
                self.gemini_client = genai.Client(api_key=gemini_key)
                logger.info("Gemini client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
        
        if openai_key and openai_key != "your_openai_api_key":
            logger.info("Initializing OpenAI client...")
            try:
                self.openai_client = OpenAI(api_key=openai_key)
                logger.info("OpenAI client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")

    def load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading history: {e}")
                return []
        return []

    def generate_response(self, prompt, system_instruction="You are a helpful assistant."):
        """通用 LLM 回應生成"""
        if not self.gemini_client and not self.openai_client:
            return "錯誤：未設定有效的 API 金鑰。"

        try:
            model_name = self.config.get('model', 'gemini-2.5-flash')
            
            # Use OpenAI if specified and client is available
            if self.openai_client and ('gpt' in model_name or not self.gemini_client):
                response = self.openai_client.chat.completions.create(
                    model=model_name if 'gpt' in model_name else 'gpt-4o',
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.config.get('temperature', 0.3)
                )
                return response.choices[0].message.content
            
            # Use Gemini as default or if specified
            elif self.gemini_client:
                if 'gemini' not in model_name:
                    model_name = 'gemini-2.5-flash'
                
                response = self.gemini_client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=self.config.get('temperature', 0.3)
                    )
                )
                return response.text
            else:
                return "錯誤：找不到可用的 LLM 客戶端。"
        except Exception as e:
            logger.error(f"Generation error: {e}")
            return f"生成回應時發生錯誤: {e}"

    def save_history(self):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving history: {e}")

    def load_today_news(self):
        """載入當日累積的新聞"""
        if os.path.exists(self.today_news_file):
            try:
                with open(self.today_news_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 檢查日期，如果不是今天則清空
                    last_update = data.get("date")
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    if last_update == today_str:
                        return data.get("news", [])
                    else:
                        logger.info("檢測到日期變更，重置當日新聞列表。")
                        return []
            except Exception as e:
                logger.error(f"Error loading today news: {e}")
                return []
        return []

    def save_today_news(self):
        """儲存當日累積的新聞"""
        try:
            today_str = datetime.now().strftime("%Y-%m-%d")
            # 移除不可序列化的 datetime 物件
            serializable_news = []
            for item in self.today_news:
                clean_item = {k: v for k, v in item.items() if k != '_dt'}
                serializable_news.append(clean_item)
                
            data = {
                "date": today_str,
                "news": serializable_news
            }
            with open(self.today_news_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving today news: {e}")

    def save_trend(self, avg_sentiment, count):
        trend_data = []
        if os.path.exists(self.trend_file):
            with open(self.trend_file, 'r', encoding='utf-8') as f:
                trend_data = json.load(f)
        
        trend_data.append({
            "timestamp": datetime.now().isoformat(),
            "average_sentiment": avg_sentiment,
            "news_count": count
        })
        
        with open(self.trend_file, 'w', encoding='utf-8') as f:
            json.dump(trend_data, f, ensure_ascii=False, indent=2)

    def is_new(self, url):
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        if url_hash in self.history:
            return False
        self.history.append(url_hash)
        if len(self.history) > 1000:
            self.history = self.history[-1000:]
        return True

    def filter_by_keywords(self, news_items):
        """實作 48 小時時間過濾，確保回頭抓取較舊的新聞。"""
        filtered = []
        now = datetime.now()
        forty_eight_hours_ago = now - timedelta(hours=48)
        
        # 載入上次紀錄的最新新聞時間 (僅作參考)
        last_pub_file = 'data/last_pub_time.txt'
        last_max_dt = forty_eight_hours_ago
        if os.path.exists(last_pub_file):
            try:
                with open(last_pub_file, 'r') as f:
                    last_max_dt = datetime.fromisoformat(f.read().strip())
            except: pass

        current_max_dt = last_max_dt

        for item in news_items:
            published_str = item.get('published', '')
            item['_dt'] = datetime.min
            
            if published_str:
                try:
                    import dateutil.parser
                    pub_dt = dateutil.parser.parse(published_str)
                    if pub_dt.tzinfo:
                        pub_dt = pub_dt.astimezone().replace(tzinfo=None)
                    else:
                        pub_dt = pub_dt.replace(tzinfo=None)
                    
                    item['_dt'] = pub_dt
                    item['display_time'] = pub_dt.strftime("%m/%d %H:%M")
                except:
                    continue
            else:
                continue

            # --- 時間過濾邏輯 ---
            # 1. 必須在 48 小時內 (保證時效性)
            if pub_dt < forty_eight_hours_ago:
                continue
            
            # 2. 更新本次運行看到的最高時間紀錄 (僅作參考)
            if pub_dt > current_max_dt:
                current_max_dt = pub_dt

            # 3. 關鍵字檢查
            content = (item.get('title', '') + " " + item.get('summary', '')).lower()
            keyword_match = any(kw.lower() in content for kw in self.keywords)
            
            if not keyword_match:
                continue

            # 4. 去重檢查 (Link MD5)
            if self.is_new(item['link']):
                filtered.append(item)
        
        # 儲存新的時間標竿
        if current_max_dt > last_max_dt:
            with open(last_pub_file, 'w') as f:
                f.write(current_max_dt.isoformat())

        filtered.sort(key=lambda x: x.get('_dt', datetime.min), reverse=True)
        return filtered

    def summarize(self, items):
        # 1. 累積當日新聞
        existing_links = {news['link'] for news in self.today_news}
        new_unique_items = [item for item in items if item['link'] not in existing_links]
        
        # 判斷是否有新新聞
        has_new_content = len(new_unique_items) > 0
        
        if has_new_content:
            self.today_news.extend(new_unique_items)
            self.save_today_news()

        if not self.today_news:
            return "目前沒有相關的新聞內容。"
        
        # 2. 如果沒有新新聞，實作「持平」邏輯
        if not has_new_content:
            logger.info("本時段無新新聞，指數將持平顯示。")
            trend_data = []
            if os.path.exists(self.trend_file):
                with open(self.trend_file, 'r', encoding='utf-8') as f:
                    trend_data = json.load(f)
            
            if trend_data:
                last_val = trend_data[-1]['average_sentiment']
                self.save_trend(last_val, len(self.today_news))
            
            # 返回最後一次生成的摘要 (從 summaries_history.json 讀取或直接回傳提示)
            return None # 回傳 None 代表不需要更新摘要文字，僅更新趨勢

        if not self.gemini_client and not self.openai_client:
            return "錯誤：未設定有效的 API 金鑰，無法生成摘要。"

        # 3. 使用當日所有累積新聞進行分析
        combined_text = ""
        sorted_today_news = sorted(self.today_news, key=lambda x: x.get('_dt', datetime.min), reverse=True)
        
        for i, item in enumerate(sorted_today_news):
            time_info = f"[{item.get('display_time', '今日')}]"
            combined_text += f"{time_info} 來源: {item['source']} | 標題: {item['title']}\n摘要: {item['summary']}\n---\n"

        prompt = (
            "你現在是資深財經分析師。請**直接開始**分析，禁止任何開場白或自我介紹。\n"
            "**絕對禁止**出現以下句子或類似語氣：\n"
            "- 身為資深財經分析師...\n"
            "- 針對今日新聞資訊...\n"
            "- 好的，我將為您彙整...\n\n"
            "請針對以下「今日累積」的所有新聞資訊進行綜合處理，並更新最新的信心指數：\n\n"
            "1. **重點摘要**：彙整今日最重要的財經動態，條列式呈現，保留原始發佈時間(如 [14:30])。\n"
            "2. **情緒評分**：標註情緒 (-1.0 到 +1.0)。\n"
            "3. **信心指標**：給出一個今日整體市場信心指數 (0 到 100)。\n\n"
            "**輸出格式規範（請務必在區塊間增加雙換行，標題請使用 H4 級別）**：\n"
            "#### 今日財經要聞\n"
            "(內容...)\n\n"
            "#### 核心動態分析與情緒\n"
            "(內容...)\n\n"
            "#### 今日市場信心指數\n"
            "信心指數：(數字)\n\n"
            f"原始資料：\n{combined_text}"
        )

        try:
            model_name = self.config.get('model', 'gemini-2.5-flash')
            if 'gemini' not in model_name:
                model_name = 'gemini-2.5-flash'

            if self.gemini_client:
                response = self.gemini_client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                summary = response.text
            else:
                response = self.openai_client.chat.completions.create(
                    model=self.config.get('model', 'gpt-4o'),
                    messages=[
                        {"role": "system", "content": "You are a professional financial analyst. NEVER use introductory phrases. Start directly with the analysis. Sentiment index should be 0-100."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3
                )
                summary = response.choices[0].message.content
            
            # --- 強效後處理：剔除自介並保留中間空行 ---
            import re
            intro_patterns = [
                r"^身為.*分析師.*",
                r"^針對今日.*",
                r"^我的處理.*",
                r"^彙整如下.*",
                r"^好的.*",
                r"^以下是.*",
                r"^作為資深.*",
                r"^我將針對.*"
            ]
            
            lines = summary.split('\n')
            processed_lines = []
            skip_intro = True
            for line in lines:
                stripped = line.strip()
                if skip_intro:
                    if not stripped: continue
                    matched = False
                    for pattern in intro_patterns:
                        if re.match(pattern, stripped):
                            matched = True
                            break
                    if matched: continue
                    else: skip_intro = False
                processed_lines.append(line)
            
            summary = '\n'.join(processed_lines).strip()
            
            # Robust extraction of overall sentiment for trend saving
            import re
            sentiment_match = re.search(r"信心指數[：:為\s]*\**(\d+(\.\d+)?)\**", summary)
            if not sentiment_match:
                sentiment_match = re.search(r"信心指數.{0,50}?\**(\d+(\.\d+)?)\**", summary, re.DOTALL)

            if sentiment_match:
                avg_val = float(sentiment_match.group(1))
                if -1.0 <= avg_val <= 1.0 and avg_val != 0:
                    avg_val = round((avg_val + 1) * 50)
                
                logger.info(f"Extracted sentiment index (accumulated): {avg_val}")
                self.save_trend(avg_val, len(self.today_news))
            
            self.save_history()
            return summary
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            return f"生成摘要時發生錯誤: {e}"
