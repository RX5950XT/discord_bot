# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import openai
import os
from dotenv import load_dotenv
import requests
from urllib.parse import quote
from datetime import datetime
import pytz
import re
import random
import base64
from io import BytesIO

# 載入環境變數
load_dotenv()

# 設置 Discord 機器人
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# 設置 OpenRouter API
client = openai.OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

# 設置 Serper API
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
SERPER_API_URL = "https://google.serper.dev/search"

# 除錯：檢查 API 金鑰
print(f"SERPER_API_KEY: {SERPER_API_KEY}")

# 意圖識別功能
class IntentClassifier:
    def __init__(self):
        # 意圖識別的關鍵詞模式
        self.intent_patterns = {
            'greeting': [
                r'\b(嗨|你好|哈囉|早安|午安|晚安|安安|hi|hello|hey|good morning|good afternoon|good evening)\b',
                r'\b(how are you|你好嗎|最近如何|近來好嗎)\b',
                r'^(hi|hello|嗨|你好)$',  # 單純的問候
                r'\b(晚上好|早上好|中午好)\b'
            ],
            'casual_chat': [
                r'\b(謝謝|感謝|thank you|thanks|thx|3q)\b',
                r'\b(再見|掰掰|拜拜|goodbye|bye|see you|掰)\b',
                r'\b(沒事|算了|forget it|never mind|沒關係)\b',
                r'\b(哈哈|呵呵|笑|lol|haha|哈|笑死|好笑)\b',
                r'\b(好的|ok|okay|收到|了解|知道了|got it)\b',
                r'\b(不錯|很棒|厲害|amazing|great|awesome|cool)\b'
            ],
            'personal_question': [
                r'\b(你是誰|你的名字|what\'s your name|who are you|你叫什麼)\b',
                r'\b(你會什麼|你能做什麼|what can you do|你的功能)\b',
                r'\b(你怎麼樣|你好嗎|how are you|你還好嗎)\b',
                r'\b(介紹一下|自我介紹|introduce yourself)\b'
            ],
            'need_search': [
                r'\b(現在|目前|最新|最近|today|current|latest|recent|即時)\b',
                r'\b(天氣|weather|溫度|temperature|氣溫|下雨)\b',
                r'\b(新聞|news|消息|事件|event|資訊|情報)\b',
                r'\b(股價|股票|匯率|price|stock|exchange rate|投資)\b',
                r'\b(什麼時候|when|何時)\b.*\b(發生|happened|occur)\b',
                r'\b(哪裡|where|地點|location|在哪)\b',
                r'[？?].*\b(是什麼|what is|what are|怎麼|如何|why|為什麼)\b',
                r'\b(教學|tutorial|怎麼做|how to|步驟|方法)\b',
                r'\b(解釋|explain|說明|告訴我|tell me)\b'
            ]
        }
    
    def classify_intent(self, message):
        """意圖識別 - 判斷訊息類型"""
        message_lower = message.lower()
        
        # 檢查各種意圖模式
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    return intent
        
        # 其他所有情況預設為需要搜尋
        return 'need_search'

# 創建意圖分類器實例
intent_classifier = IntentClassifier()

# 獲取當前時間
def get_current_time(timezone="Asia/Taipei"):
    """獲取指定時區的當前時間"""
    try:
        tz = pytz.timezone(timezone)
        current_time = datetime.now(tz).strftime("%Y年%m月%d日 %H:%M:%S %Z")
        return current_time
    except Exception as e:
        return f"無法獲取時間：{str(e)}"

# 執行 Serper API 搜尋
def search_web(query):
    """使用 Serper API 進行網路搜尋並返回結果"""
    try:
        headers = {
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "q": query,
            "num": 10  # 限制搜尋結果數量
        }
        response = requests.post(SERPER_API_URL, json=payload, headers=headers)
        response.raise_for_status()  # 檢查 HTTP 錯誤
        print(f"搜尋請求 URL: {response.url}")  # 除錯：記錄請求 URL
        data = response.json()
        
        # 提取搜尋結果
        results = data.get('organic', [])
        search_results = []
        for result in results[:10]:  # 限制為前 10 個結果
            title = result.get('title', '無標題')
            snippet = result.get('snippet', '無描述')
            url = result.get('link', '無連結')
            search_results.append(f"標題: {title}\n描述: {snippet}\n連結: {url}\n")
        
        search_output = "\n".join(search_results) if search_results else "無搜尋結果"
        print(f"搜尋結果：{search_output}")  # 除錯：記錄搜尋結果
        return search_output
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP 錯誤：{str(http_err)}")  # 除錯
        return f"搜尋時發生 HTTP 錯誤：{str(http_err)}"
    except Exception as e:
        print(f"搜尋錯誤：{str(e)}")  # 除錯
        return f"搜尋時發生錯誤：{str(e)}"

# 當機器人啟動時
@bot.event
async def on_ready():
    print(f'已登入為 {bot.user}')

# 聊天與搜尋指令（加入意圖識別及圖片處理）
@bot.command()
async def chat(ctx, *, message=None):
    """處理用戶的聊天請求，結合意圖識別、圖片處理、Serper API 搜尋、當前時間與AI回應"""
    try:
        # 檢查是否有附加圖片
        has_image = False
        image_urls = []
        image_descriptions = []
        
        # 檢查訊息中的附件
        if ctx.message.attachments:
            for attachment in ctx.message.attachments:
                if attachment.content_type and attachment.content_type.startswith('image/'):
                    has_image = True
                    image_urls.append(attachment.url)
                    print(f"檢測到圖片附件：{attachment.filename}")
        
        if not message and not has_image:
            await ctx.send("哎呀，你忘了告訴我你想聊什麼！😅 請用 `!chat 你的問題` 試試，或者附上一張圖片！")
            return
        
        if not message:
            message = "請描述這張圖片"
        
        # 獲取當前時間（台北時區）
        current_time = get_current_time("Asia/Taipei")
        
        # 記錄用戶資訊
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 用戶: {ctx.author.name}")
        print(f"訊息: {message}")
        
        if has_image:
            print(f"包含圖片: {len(image_urls)} 張")
            
            # 使用AI處理圖片
            system_content = "你是一個友善且知識淵博的AI助手，擅長分析圖片。請用繁體中文回答，並保持輕鬆有趣的語氣！😎"
            
            messages = [{"role": "system", "content": system_content}]
            
            # 準備包含圖片的訊息
            user_message = {
                "role": "user",
                "content": [
                    {
                        "type": "text", 
                        "text": f"""
用戶問題：{message}
當前時間（台北時區）：{current_time}

請仔細觀察圖片內容，以繁體中文提供一個友善、詳細且有趣的回答！😎
分析圖片中的主要內容、場景、人物或物品，並根據用戶的問題做出回應。
"""
                    }
                ]
            }
            
            # 添加所有圖片到用戶訊息中
            for img_url in image_urls:
                try:
                    response = requests.get(img_url)
                    if response.status_code == 200:
                        # 獲取圖片數據並轉為base64
                        img_data = response.content
                        img_base64 = base64.b64encode(img_data).decode('utf-8')
                        
                        # 添加圖片到訊息
                        user_message["content"].append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{response.headers.get('Content-Type', 'image/jpeg')};base64,{img_base64}"
                            }
                        })
                except Exception as e:
                    print(f"圖片處理錯誤：{str(e)}")
            
            messages.append(user_message)
            
            # 呼叫 OpenRouter API 進行圖片分析
            print("使用AI處理圖片...")
            response = client.chat.completions.create(
                model="google/gemma-3-27b-it:free",  # 使用支援圖像的模型
                messages=messages,
                max_tokens=2000,
                temperature=1,
                extra_headers={
                    "HTTP-Referer": "",  # 可替換為你的網站
                    "X-Title": quote("")  # 使用 URL 編碼
                }
            )
            
        else:
            # 沒有圖片，進行正常的文字處理
            # 意圖識別
            intent = intent_classifier.classify_intent(message)
            print(f"識別意圖: {intent}")
            print(f"是否需要搜尋: {'否' if intent in ['greeting', 'casual_chat', 'personal_question'] else '是'}")
            print("-" * 50)
            
            # 根據意圖決定是否使用搜尋
            if intent in ['greeting', 'casual_chat', 'personal_question']:
                # 不進行網路搜尋，直接使用 OpenRouter API
                system_content = "你是一個友善且知識淵博的AI助手，會用繁體中文簡潔地回答問題，並保持輕鬆有趣的語氣！😎"
                
                # 準備提示，只包含用戶問題和當前時間
                prompt = f"""
用戶問題：{message}
當前時間（台北時區）：{current_time}

請以繁體中文提供一個友善、簡潔且有趣的回答！😎
如果問題涉及時間，請明確提及當前時間。
"""
                max_tokens = 2000
                
            else:
                # 需要搜尋
                # 執行 Serper API 搜尋
                search_results = search_web(message)
                
                # 檢查是否為時間相關查詢
                time_keywords = ["時間", "現在", "今天", "日期"]
                is_time_query = any(keyword in message for keyword in time_keywords)
                
                # 設定系統提示
                system_content = "你是一個友善且知識淵博的AI助手，會用繁體中文回答，並保持輕鬆有趣的語氣！😎 對於需要最新資訊的問題，請充分利用提供的搜尋結果。"
                
                # 準備提示，包含搜尋結果和當前時間
                prompt = f"""
用戶問題：{message}
當前時間（台北時區）：{current_time}
搜尋結果：
{search_results}

請根據用戶的問題、當前時間和提供的搜尋結果，以繁體中文提供一個友善、知識淵博且有趣的回答！😎
如果問題涉及時間，請明確提及當前時間。
如果搜尋結果不足以回答問題，請依據你的知識給出最佳回答，並說明可能需要更多資訊。
"""
                max_tokens = 2000
            
            # 呼叫 OpenRouter API 進行聊天
            print("使用AI處理文字訊息...")
            response = client.chat.completions.create(
                model="deepseek/deepseek-chat-v3-0324:free",
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=1,
                extra_headers={
                    "HTTP-Referer": "",  # 可替換為你的網站
                    "X-Title": quote("")  # 使用 URL 編碼
                }
            )
        
        # 除錯：記錄 OpenRouter 回應
        print(f"OpenRouter 回應：{response.choices[0].message.content}")
        
        # 回傳 AI 的回應
        await ctx.send(response.choices[0].message.content)
    
    except Exception as e:
        print(f"錯誤：{str(e)}")  # 除錯
        await ctx.send(f"哎呀，出了點小問題：{str(e)} 😅 請再試一次！")

# 意圖測試指令
@bot.command()
async def intent(ctx, *, message):
    """測試意圖識別功能"""
    intent = intent_classifier.classify_intent(message)
    need_search = intent not in ['greeting', 'casual_chat', 'personal_question']
    
    embed = discord.Embed(title="意圖識別結果", color=0x00ff00)
    embed.add_field(name="輸入訊息", value=message, inline=False)
    embed.add_field(name="識別意圖", value=intent, inline=True)
    embed.add_field(name="需要搜尋", value="是" if need_search else "否", inline=True)
    
    await ctx.send(embed=embed)

# 幫助指令
@bot.command()
async def help_bot(ctx):
    """顯示機器人功能說明"""
    embed = discord.Embed(title="🤖 AI 聊天機器人功能說明", description="這是一個具備智能意圖識別與圖片處理的聊天機器人！", color=0x0099ff)
    
    embed.add_field(name="📝 主要指令", value="""
`!chat <訊息>` - 與AI聊天（會自動判斷是否需要搜尋）
`!chat` + 圖片附件 - 分析圖片內容
`!intent <訊息>` - 測試意圖識別功能
`!help_bot` - 顯示此幫助訊息
    """, inline=False)
    
    embed.add_field(name="🧠 智能意圖識別", value="""
機器人會自動判斷你的問題類型：
• **問候語** - 嗨、你好、早安等 → 直接使用AI回應，不進行網路搜尋
• **一般對話** - 謝謝、再見等 → 直接使用AI回應，不進行網路搜尋
• **個人問題** - 你是誰、你會什麼等 → 直接使用AI回應，不進行網路搜尋
• **需要搜尋** - 複雜問題、最新資訊等 → 使用搜尋+AI回應
    """, inline=False)
    
    embed.add_field(name="🖼️ 圖片處理功能", value="""
• 支持上傳圖片附件進行分析
• 使用 AI 模型處理圖像內容
• 可以加上問題或描述以獲取更精確的圖片分析
• 例如：`!chat 這是什麼動物？` + 圖片附件
    """, inline=False)
    
    embed.add_field(name="💡 使用範例", value="""
`!chat 你好` - 簡單問候，直接回應
`!chat 謝謝你的幫助` - 感謝話語，直接回應
`!chat 現在台北的天氣如何？` - 需要搜尋的問題
`!chat` + 照片 - 分析照片內容
`!chat 這張圖片是哪個城市？` + 照片 - 帶問題的圖片分析
`!intent 早安` - 測試意圖識別
    """, inline=False)
    
    embed.add_field(name="⚡ 優勢特色", value="""
✅ 智能判斷 - 自動決定處理方式
✅ 圖像識別 - 支援圖片分析功能
✅ 靈活回應 - 全部使用AI生成回答
✅ 詳細日誌 - 記錄處理過程
    """, inline=False)
    
    await ctx.send(embed=embed)

# 監聽所有訊息（用於自動意圖識別）
@bot.event
async def on_message(message):
    # 忽略機器人自己的訊息
    if message.author == bot.user:
        return
    
    # 如果訊息提到機器人或是私訊，自動進行意圖識別並回應
    if bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        # 檢查是否有圖片
        has_image = False
        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type and attachment.content_type.startswith('image/'):
                    has_image = True
                    break
        
        # 移除提及部分，只保留實際訊息內容
        content = message.content
        if bot.user.mentioned_in(message):
            content = content.replace(f'<@{bot.user.id}>', '').strip()
        
        if content or has_image:  # 確保有實際內容或圖片
            if has_image:
                # 有圖片附件
                img_command = "這張圖片"
                if content:
                    img_command = content
                await message.reply(f"我看到了一張圖片！請使用 `!chat {img_command}` 來獲得我的分析！ 📸")
            else:
                # 只有文字
                intent = intent_classifier.classify_intent(content)
                print(f"[自動回應] 用戶: {message.author.name}, 訊息: {content}, 意圖: {intent}")
                await message.reply(f"請使用 `!chat {content}` 來獲得我的回答！ 😊")
        else:
            await message.reply("你好！有什麼我可以幫助你的嗎？使用 `!help_bot` 查看我的功能！")
    
    # 處理指令
    await bot.process_commands(message)

# 啟動機器人
bot.run(os.getenv("DISCORD_BOT_TOKEN"))