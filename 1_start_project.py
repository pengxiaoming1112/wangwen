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
TIMEOUT_SECONDS = 300 

client = None
START_WORK_TIME = time.time()

# --- 2. 品牌与视觉工具 ---

def print_brand_header():
    print(r"""
    *********************************************************
    * 🌟 奥特曼空投研究院·网文矩阵启动器 V3.2 🌟        *
    * Ultraman Airdrop Research Institute (PX-Chain)      *
    *********************************************************
    """)

def print_brand_end():
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
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_work_duration():
    seconds = int(time.time() - START_WORK_TIME)
    m, s = divmod(seconds, 60)
    return f"{m}分 {s}秒"

def heartbeat(stop_event, task_name):
    start_wait = time.time()
    while not stop_event.is_set():
        time.sleep(1)
        elapsed = int(time.time() - start_wait)
        if elapsed > 0 and elapsed % 15 == 0:
            sys.stdout.write(f"\r⏳ [奥特曼思考中...] {task_name} 已耗时 {elapsed} 秒...   ")
            sys.stdout.flush()

def sanitize_filename(name):
    return "".join([c for c in name if c.isalnum() or c in (' ', '_', '-') or '\u4e00' <= c <= '\u9fa5']).strip()

def create_temp_folder(book_title):
    """创建临时文件夹 (带时间戳，防止冲突)"""
    timestamp = time.strftime("%Y%m%d_%H%M")
    clean_title = sanitize_filename(book_title)
    if len(clean_title) > 50: clean_title = clean_title[:50]
    
    folder_name = f"Book_{timestamp}_{clean_title}"
    
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        os.makedirs(f"{folder_name}/chapters")
    
    return folder_name

def finalize_folder_name(current_path, book_title):
    """
    🔥 核心升级：正名仪式
    尝试将文件夹重命名为纯净的 Book_书名
    """
    clean_title = sanitize_filename(book_title)
    if len(clean_title) > 50: clean_title = clean_title[:50]
    
    target_name = f"Book_{clean_title}"
    target_path = os.path.join(os.path.dirname(current_path), target_name)
    
    # 如果目标名字没被占用，就改名
    if not os.path.exists(target_path):
        try:
            os.rename(current_path, target_path)
            log(f"✨ 文件夹已正名为: {target_name}")
            return target_path
        except Exception as e:
            log(f"⚠️ 正名失败 ({e})，保持原名")
            return current_path
    else:
        log(f"⚠️ 检测到同名书籍 {target_name} 已存在，保持时间戳后缀以示区别。")
        return current_path

def call_ai(system_prompt, user_prompt, task_name="计算中"):
    global client
    if client is None: return None

    stop_heartbeat = threading.Event()
    t = threading.Thread(target=heartbeat, args=(stop_heartbeat, task_name))
    t.daemon = True
    
    try:
        t.start()
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
        sys.stdout.write("\r" + " " * 80 + "\r")
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
        try:
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump({"used_ideas": []}, f)
        except Exception:
            pass

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

# --- 4. Agent 逻辑 ---

def agent0_brainstorm(tag):
    log(f"(Agent 0) 正在思考【{tag}】题材的创意...")
    db = load_db()
    history = db["used_ideas"][-10:] 
    history_str = "\n".join(history) if history else "无"

    system_prompt = """
    你是一位网文总编，擅长发掘【幽默风趣、脑洞大开】的爆款创意。
    请生成 3 个全新的小说创意。
    【格式要求】：仅输出 JSON，包含 ideas 列表 (title, logline)。
    """
    user_prompt = f"标签：{tag}\n请避开：{history_str}"
    
    res = call_ai(system_prompt, user_prompt, task_name="脑暴创意")
    if res:
        clean_res = res.replace("```json", "").replace("```", "").strip()
        try:
            data = json.loads(clean_res)
            return data.get("ideas", [])
        except:
            return []
    return []

def agent1_bible(idea, word_count):
    print("\n")
    log(f"(Agent 1) 正在构建世界观 (目标 {word_count} 字)...")
    prompt = f"""
    你是一位白金级网文架构师。
    任务：根据【创意】写一份《项目白皮书》。
    【核心风格】：幽默、风趣、爽快，符合中国读者习惯。
    【篇幅】：{word_count} 字长篇。
    【输出结构】：书名、梗概、世界观、人设、爽点。
    """
    return call_ai(prompt, f"创意核心：{idea}", task_name="构建世界观")

def agent2_outline(bible_content, chapter_count):
    print("\n")
    log(f"(Agent 2) 正在拆解 {chapter_count} 章细纲...")
    prompt = f"""
    你是一位网文主编。
    【任务】：生成 {chapter_count} 章细纲。
    【要求】：节奏跌宕起伏，反套路，每行一章，纯净格式。
    """
    return call_ai(prompt, f"【白皮书内容】：\n{bible_content}", task_name="生成大纲")

# --- 5. 主程序 ---

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
    print_brand_header() 
    init_db_test() 
    init_client_dynamic() 
    
    tag = input("\n🎯 请输入标签 (如: 历史/玄幻): ") or "玄幻"
    
    ideas = agent0_brainstorm(tag)
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
        selected_idea = input("请输入创意: ")

    total_words = random.randint(110, 200) * 1000 
    chapter_limit = int(total_words / 2300)
    print(f"\n⚙️  系统锁定: 目标 {total_words} 字 | 预计 {chapter_limit} 章")
    
    bible = agent1_bible(selected_idea, total_words)
    if not bible: return
    
    try:
        book_title = bible.split('\n')[0].replace("书名：", "").replace("《", "").replace("》", "").strip()
    except:
        book_title = "新书项目"
    
    # 1. 先创建临时文件夹
    folder_path = create_temp_folder(book_title)
    
    with open(f"{folder_path}/bible.txt", "w", encoding="utf-8") as f:
        f.write(bible)
    
    outline = agent2_outline(bible, chapter_limit)
    if outline:
        with open(f"{folder_path}/outline.txt", "w", encoding="utf-8") as f:
            f.write(outline)
    
    # 2. 资料生成完毕，执行正名仪式
    final_path = finalize_folder_name(folder_path, book_title)
    
    print(f"\n📂 策划资料已归档: {final_path}")
    print(f"⏱️ 本次策划耗时: {get_work_duration()}")
    print_brand_end() 

if __name__ == "__main__":
    start_new_project()