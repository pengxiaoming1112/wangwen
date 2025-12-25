import os
import time
import random
import json
import threading
import datetime
import sys
from openai import OpenAI

# --- 1. 全局配置区 ---
MODEL_NAME = "gemini-3-pro-preview"
DB_FILE = "matrix_db.json" 
TIMEOUT_SECONDS = 300 # 单次请求超时时间

# 初始化 client
client = None
START_WORK_TIME = time.time() # 记录启动时间

# --- 2. 品牌与视觉工具 ---

def print_brand_header():
    print(r"""
    *********************************************************
    * 🌟 奥特曼空投研究院·网文矩阵启动器 V3.0 🌟        *
    * Ultraman Airdrop Research Institute (PX-Chain)      *
    *********************************************************
    """)

def print_brand_end():
    # 你的专属定制 Logo
    print(r"""
           / \      / \
          /   \____/   \   <-- 灵感注入完成
         /  (O)    (O)  \
        |                |
        | 奥特曼空投研究院 |
        |    pxm_chain   |
         \              /
          \____________/
             |  |  |
             |_ |_ |
      
    ✨ 策划任务完成！项目已归档。
    """)

def log(msg):
    """打印带时间的日志"""
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_work_duration():
    """计算工作时长"""
    seconds = int(time.time() - START_WORK_TIME)
    m, s = divmod(seconds, 60)
    return f"{m}分 {s}秒"

def heartbeat(stop_event, task_name):
    """心跳线程：防止用户以为死机"""
    start_wait = time.time()
    while not stop_event.is_set():
        time.sleep(1)
        elapsed = int(time.time() - start_wait)
        if elapsed > 0 and elapsed % 15 == 0:
            sys.stdout.write(f"\r⏳ [奥特曼思考中...] {task_name} 已耗时 {elapsed} 秒...   ")
            sys.stdout.flush()

def sanitize_filename(name):
    return "".join([c for c in name if c.isalnum() or c in (' ', '_', '-')]).strip()

def create_book_folder(book_title):
    timestamp = time.strftime("%Y%m%d_%H%M")
    clean_title = sanitize_filename(book_title)
    if len(clean_title) > 15: clean_title = clean_title[:15]
    
    folder_name = f"Book_{timestamp}_{clean_title}"
    
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        os.makedirs(f"{folder_name}/chapters")
    
    return folder_name

def call_ai(system_prompt, user_prompt, task_name="计算中"):
    """
    统一 AI 接口 (带心跳动画)
    """
    global client
    if client is None: return None

    stop_heartbeat = threading.Event()
    t = threading.Thread(target=heartbeat, args=(stop_heartbeat, task_name))
    t.daemon = True
    
    try:
        t.start() # 启动心跳
        
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            timeout=TIMEOUT_SECONDS 
        )
        
        stop_heartbeat.set()
        t.join()
        sys.stdout.write("\r" + " " * 80 + "\r") # 清除心跳行
        
        return response.choices[0].message.content

    except Exception as e:
        stop_heartbeat.set()
        t.join()
        sys.stdout.write("\r" + " " * 80 + "\r")
        log(f"❌ AI调用出错: {e}")
        return None

# --- 3. 数据库管理 ---

def init_db_test():
    if not os.path.exists(DB_FILE):
        # log(f"检测到没有数据库，正在创建 {DB_FILE}...")
        try:
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump({"used_ideas": []}, f)
            # log("✅ 数据库文件创建成功！")
        except Exception as e:
            log(f"❌ 严重错误：无法创建文件，请检查权限。报错：{e}")

def load_db():
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"used_ideas": []}

def save_to_db(idea_summary):
    data = load_db()
    data["used_ideas"].append(idea_summary)
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- 4. Agent 0: 创意脑暴师 ---

def agent0_brainstorm(tag):
    log(f"(Agent 0) 正在思考【{tag}】题材的创意...")
    
    db = load_db()
    history = db["used_ideas"][-10:] 
    history_str = "\n".join(history) if history else "无"

    # 注入了“风格要求”
    system_prompt = """
    你是一位网文总编，擅长发掘【幽默风趣、脑洞大开】的爆款创意。
    请生成 3 个全新的小说创意。
    
    【风格要求】：
    1. 必须符合中国网文读者的阅读习惯，通俗易懂。
    2. 设定要有趣，最好能带点“梗”或反差萌。
    
    【格式要求】：
    请仅输出一段纯粹的 JSON 代码，不要包含 ```json 这种标记。
    格式如下：
    {
      "ideas": [
        {"title": "书名1", "logline": "简介1"},
        {"title": "书名2", "logline": "简介2"},
        {"title": "书名3", "logline": "简介3"}
      ]
    }
    """
    
    user_prompt = f"标签：{tag}\n请避开：{history_str}"
    
    res = call_ai(system_prompt, user_prompt, task_name="脑暴创意")
    
    if res:
        clean_res = res.replace("```json", "").replace("```", "").strip()
        try:
            data = json.loads(clean_res)
            return data.get("ideas", [])
        except:
            log("⚠️ JSON解析失败，转为手动模式")
            return []
    return []

# --- 5. Agent 1 & 2 (注入了幽默风格) ---

def agent1_bible(idea, word_count):
    print("\n")
    log(f"(Agent 1) 正在构建世界观 (目标 {word_count} 字)...")
    
    prompt = f"""
    你是一位白金级网文架构师。
    任务：根据【创意】写一份《项目白皮书》。
    
    【核心风格指令】：
    全书基调必须是【幽默、风趣、爽快】。
    1. 拒绝沉闷的说明书式描写，用生动有趣的语言来设定世界。
    2. 主角性格要有意思（例如：腹黑、吐槽役、或有某种奇葩执念），拒绝苦大仇深。
    3. 符合中国读者的阅读习惯，不要翻译腔。
    
    【篇幅硬性要求】：
    本作为 {word_count} 字的长篇网文。请设计【多层级的地图】确保剧情够长。
    
    【输出结构】：
    1. 书名 (严禁带《》)
    2. 一句话核心梗概
    3. 世界观与力量体系 (分等级，力量名称要帅)
    4. 主角与反派人设 (要有反差感)
    5. 三大核心爽点 (要具体)
    """
    return call_ai(prompt, f"创意核心：{idea}", task_name="构建世界观")

def agent2_outline(bible_content, chapter_count):
    print("\n")
    log(f"(Agent 2) 正在拆解 {chapter_count} 章细纲...")
    prompt = f"""
    你是一位网文主编。请基于《项目白皮书》生成全书细纲。
    
    【核心风格指令】：
    剧情要【跌宕起伏且充满笑点】。
    每一章的剧情简介都要写得吸引人，不要写流水账。
    在紧张的冲突中，适当穿插主角的骚操作或幽默互动。
    
    【硬性指标】：
    1. 必须生成严格的 {chapter_count} 章。
    2. 节奏控制：每 10-15 章设计一个小高潮。剧情要反套路，要狗血，要让读者猜不到。不要写四平八稳的流水账，多安排一些误会、打脸和神转折。
    3. 格式纯净：每一行只写一章的剧情，不要前言后语，不要序号。
    """
    return call_ai(prompt, f"【白皮书内容】：\n{bible_content}", task_name="生成大纲")

# --- 6. 主程序 ---

def init_client_dynamic():
    global client
    print("\n🔐 --- 身份验证 ---")
    api_key = input("请输入 API Key: ").strip()
    while not api_key:
        api_key = input("请输入 API Key: ").strip()
    
    default_url = "http://172.96.160.216:3000/v1"
    base_url = input(f"Base URL (回车默认 {default_url}): ").strip() or default_url
    
    client = OpenAI(api_key=api_key, base_url=base_url)

def start_new_project():
    print_brand_header() # 1. 打印开机Logo
    init_db_test() 
    init_client_dynamic() 
    
    tag = input("\n🎯 请输入标签 (如: 历史/玄幻): ")
    if not tag: tag = "玄幻"
    
    # Agent 0
    ideas = agent0_brainstorm(tag)
    selected_idea = None
    
    if ideas:
        print("\n💡 奥特曼为您捕获了以下灵感：")
        for i, idea in enumerate(ideas):
            print(f"[{i+1}] 《{idea['title']}》: {idea['logline']}")
        
        choice = input("\n👉 请选择 (1-3): ").strip()
        idx = int(choice) - 1 if choice.isdigit() and 1 <= int(choice) <= 3 else 0
        
        selected_idea_obj = ideas[idx]
        selected_idea = f"书名：《{selected_idea_obj['title']}》\n梗概：{selected_idea_obj['logline']}"
        save_to_db(selected_idea_obj['logline'])
    else:
        print("⚠️ 自动创意未生效，请手动输入。")
        selected_idea = input("请输入创意: ")

    # 随机范围：110,000 字 到 200,000 字
    total_words = random.randint(110, 200) * 1000 
    chapter_limit = int(total_words / 2300)
    
    print(f"\n⚙️  系统锁定: 目标 {total_words} 字 | 预计 {chapter_limit} 章")
    
    # Agent 1
    bible = agent1_bible(selected_idea, total_words)
    if not bible: return
    
    # 提取书名
    try:
        book_title = bible.split('\n')[0].replace("书名：", "").replace("《", "").replace("》", "").strip()
    except:
        book_title = "新书项目"
    if len(book_title) > 20: book_title = book_title[:15]
    
    # 创建文件夹
    folder_path = create_book_folder(book_title)
    with open(f"{folder_path}/bible.txt", "w", encoding="utf-8") as f:
        f.write(bible)
    
    # Agent 2
    outline = agent2_outline(bible, chapter_limit)
    if outline:
        with open(f"{folder_path}/outline.txt", "w", encoding="utf-8") as f:
            f.write(outline)
    
    print(f"\n📂 策划资料已归档: {folder_path}")
    print(f"⏱️ 本次策划耗时: {get_work_duration()}")
    
    print_brand_end() # 2. 打印结束Logo

if __name__ == "__main__":
    start_new_project()