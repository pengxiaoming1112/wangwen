import os
import time
import sys
import datetime
import threading
from openai import OpenAI

# --- 1. 全局配置区 ---
MODEL_NAME = "gemini-3-pro-preview"
TIMEOUT_SECONDS = 1200 
client = None
START_WORK_TIME = time.time()
SESSION_START_TIME = time.time() 
CHAPTERS_WRITTEN_SESSION = 0 

# --- 2. 品牌与视觉工具 ---

def set_terminal_title(title):
    sys.stdout.write(f"\x1b]2;{title}\x07")
    sys.stdout.flush()

def print_brand_header():
    print(r"""
    ****************************************************
    * 🌟 奥特曼空投研究院专属写作引擎 V5.5 🌟      *
    * Ultraman Airdrop Research Institute       *
    ****************************************************
    """)

def print_brand_end():
    print(r"""
           / \      / \
          /   \____/   \   <-- 光之凝视
         /  (O)    (O)  \
        |                |
        | 奥特曼空投研究院 |
        |    pxm_chain   |
         \              /
          \____________/
             |  |  |
             |_ |_ |
      
    ✨ 任务完成！光之巨人已停止工作。
    """)

def log(msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_progress_bar(current, total, length=20):
    if total == 0: return ""
    percent = current / total
    filled_length = int(length * percent)
    bar = "▓" * filled_length + "░" * (length - filled_length)
    return f"[{bar}] {int(percent * 100)}%"

def calculate_book_stats(folder_path, total_chapters):
    finished_chapters = 0
    finished_words = 0
    for i in range(1, total_chapters + 1):
        file_path = f"{folder_path}/chapters/第{i}章.txt"
        if os.path.exists(file_path):
            finished_chapters += 1
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    finished_words += len(content)
            except:
                pass 
    remaining_chapters = total_chapters - finished_chapters
    estimated_remaining_words = remaining_chapters * 2500 
    return finished_chapters, finished_words, remaining_chapters, estimated_remaining_words

def print_final_statistics(folder_path, total_chapters):
    """🔥 新增：完本战绩结算页面"""
    finished_chapters, finished_words, _, _ = calculate_book_stats(folder_path, total_chapters)
    avg_words = int(finished_words / finished_chapters) if finished_chapters > 0 else 0
    
    print("\n" + "="*50)
    print("🏆 【奥特曼·完本战绩结算】 🏆")
    print("="*50)
    print(f"📚 书籍路径: {folder_path}")
    print(f"🏁 完结状态: {finished_chapters}/{total_chapters} 章")
    print(f"📝 累计字数: {finished_words} 字")
    print(f"📊 平均每章: {avg_words} 字")
    print("="*50 + "\n")

def calculate_eta(total_chapters, current_chapter_index):
    global SESSION_START_TIME, CHAPTERS_WRITTEN_SESSION
    chapters_remaining = total_chapters - current_chapter_index
    if CHAPTERS_WRITTEN_SESSION == 0:
        return f"计算中..."
    elapsed_session = time.time() - SESSION_START_TIME
    avg_time_per_chapter = elapsed_session / CHAPTERS_WRITTEN_SESSION
    eta_seconds = int(avg_time_per_chapter * chapters_remaining)
    m, s = divmod(eta_seconds, 60)
    h, m = divmod(m, 60)
    return f"{h}小时{m}分" if h > 0 else f"{m}分{s}秒"

def heartbeat(stop_event, subtitle=""):
    start_wait = time.time()
    while not stop_event.is_set():
        time.sleep(1)
        elapsed = int(time.time() - start_wait)
        if elapsed > 0 and elapsed % 15 == 0:
            sys.stdout.write(f"\r⏳ [奥特曼充能中...] AI已思考 {elapsed} 秒... ({subtitle})   ")
            sys.stdout.flush()

def countdown(seconds, message="冷却中"):
    for i in range(seconds, 0, -1):
        sys.stdout.write(f"\r⏳ [系统冷却] {message}: {i}秒... ")
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write(f"\r✅ {message}结束!        \n")

def read_file(path):
    if not os.path.exists(path): return None
    with open(path, "r", encoding="utf-8") as f: return f.read()

def is_locked(folder_path): return os.path.exists(os.path.join(folder_path, "writing.lock"))
def lock_book(folder_path):
    with open(os.path.join(folder_path, "writing.lock"), "w") as f: f.write("LOCKED")
def unlock_book(folder_path):
    lock_path = os.path.join(folder_path, "writing.lock")
    if os.path.exists(lock_path): os.remove(lock_path)

def mark_book_as_finished(folder_path, total_chapters):
    try:
        # 先打印战绩
        print_final_statistics(folder_path, total_chapters)
        
        unlock_book(folder_path)
        if folder_path.endswith("/"): folder_path = folder_path[:-1]
        
        base_name = os.path.basename(folder_path)
        dir_name = os.path.dirname(folder_path)
        new_folder_name = f"【已完结】_{base_name}"
        new_full_path = os.path.join(dir_name, new_folder_name)
        
        os.rename(folder_path, new_full_path)
        
        print(f"🎉 文件夹已自动封存为: {new_folder_name}")
        set_terminal_title(f"✅ 已完结: {base_name}")
    except Exception as e:
        print(f"\n⚠️ 完结改名失败: {e}")

# --- AI 核心 ---
def generate_chapter_robust(chapter_num, outline, prev_summary, prev_text_tail, bible):
    global client
    clean_outline = outline.replace("\n", " ").strip()
    subtitle = clean_outline[:20] + "..." if len(clean_outline) > 20 else clean_outline

    system_prompt = """
    你是一位混迹网文圈10年的白金大神（人类），擅长用“极具网感”和“沉浸式”的笔法写作。
    你的目标是：写出的文字完全看不出是AI生成的。
    【🚫 绝对禁令】：
    1. 禁止使用“综上所述”、“总而言之”等连接词。
    2. 禁止在结尾升华主题。
    3. 禁止使用“翻译腔”。
    4. 禁止在开头自己写章节名。
    【✨ 人类拟态指南】：
    1. **口语化**：多用短句和心里吐槽。
    2. **Show, Don't Tell**：多描写动作细节。
    3. **断章狗**：结尾卡在冲突点。
    【硬性指标】：字数 2300 - 2800 字。
    """
    user_prompt = f"""
    【世界观】：{bible[:1500]}...
    【前情提要】：{prev_summary}
    【上章结尾】：...{prev_text_tail}
    【本章任务】：第 {chapter_num} 章：{outline}
    👉 请开始正文创作（直接写正文，不要写标题）：
    """
    attempt = 0
    while True:
        attempt += 1
        stop_heartbeat = threading.Event()
        t = threading.Thread(target=heartbeat, args=(stop_heartbeat, subtitle))
        t.daemon = True
        try:
            log(f"🎬 第 {chapter_num} 章：『{subtitle}』 (第 {attempt} 次尝试)...")
            t.start()
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=0.85, presence_penalty=0.6, timeout=TIMEOUT_SECONDS 
            )
            stop_heartbeat.set()
            t.join() 
            sys.stdout.write("\r" + " " * 80 + "\r")
            
            content = response.choices[0].message.content
            current_len = len(content)
            
            if content and current_len >= 1500:
                log(f"✅ 生成完毕 (字数: {current_len})")
                return content
            else:
                log(f"⚠️ 字数不足 ({current_len})，重写中...")
                time.sleep(2)
                continue
        except KeyboardInterrupt:
            stop_heartbeat.set()
            raise KeyboardInterrupt 
        except Exception as e:
            stop_heartbeat.set()
            t.join()
            sys.stdout.write("\r" + " " * 80 + "\r")
            log(f"❌ 错误: {str(e)}")
            countdown(10, "系统恢复中")

def summarize_chapter(content):
    try:
        prompt = f"请用200字总结以下章节的关键剧情：\n\n{content[:2000]}"
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            timeout=60
        )
        return response.choices[0].message.content
    except:
        return "（摘要生成失败）"

# --- 主程序 ---
def init_client_dynamic():
    global client
    print("\n🔐 --- 身份验证 ---")
    api_key = input("请输入 API Key: ").strip()
    while not api_key: api_key = input("请输入 API Key: ").strip()
    default_url = "http://172.96.160.216:3000/v1"
    base_url = input(f"Base URL (回车默认 {default_url}): ").strip() or default_url
    client = OpenAI(api_key=api_key, base_url=base_url)

def main_writer():
    global CHAPTERS_WRITTEN_SESSION, SESSION_START_TIME
    try:
        print_brand_header()
        init_client_dynamic()
        
        all_books = [d for d in os.listdir('.') if os.path.isdir(d) and d.startswith("Book_")]
        all_books.sort(reverse=True)
        if not all_books:
            print("❌ 没有找到待写书籍！")
            return

        available_books = []
        print("\n📚 待写书籍列表：")
        for i, book in enumerate(all_books):
            status = "🟢 空闲"
            if is_locked(book): status = "🔴 锁定中"
            print(f"[{i+1}] {status} : {book}")
            if not is_locked(book): available_books.append(book)
        
        print("-" * 30)
        choice = input("\n请选择序号 (输入 'auto' 自动接管): ").strip()
        folder_path = ""
        
        if choice.lower() == 'auto':
            if not available_books: return
            folder_path = available_books[0]
        else:
            if choice.isdigit() and 1 <= int(choice) <= len(all_books):
                target_book = all_books[int(choice)-1]
                if is_locked(target_book):
                    if input("⚠️ 强制接管？(y/n): ").lower() != 'y': return
                    unlock_book(target_book)
                folder_path = target_book
            else:
                return

        book_name = folder_path.replace("Book_", "").split("_")[-1]
        set_terminal_title(f"🚀 准备中: {book_name}")
        lock_book(folder_path)
        print(f"\n🔒 已锁定项目：{folder_path}")
        
        bible = read_file(f"{folder_path}/bible.txt")
        outline_raw = read_file(f"{folder_path}/outline.txt")
        
        if not bible or not outline_raw:
            print("❌ 资料缺失！")
            unlock_book(folder_path)
            return
            
        outlines = [line.strip() for line in outline_raw.split('\n') if line.strip()]
        total_chapters = len(outlines)
        
        prev_summary = "故事开始。"
        prev_tail = "无"
        SESSION_START_TIME = time.time()
        CHAPTERS_WRITTEN_SESSION = 0
        
        for i, line_content in enumerate(outlines):
            chapter_num = i + 1
            set_terminal_title(f"✍️ {book_name} | {chapter_num}/{total_chapters}")
            file_name = f"{folder_path}/chapters/第{chapter_num}章.txt"
            
            done_ch, done_words, left_ch, est_left_words = calculate_book_stats(folder_path, total_chapters)
            eta_str = calculate_eta(total_chapters, i)
            progress_bar = get_progress_bar(done_ch, total_chapters)
            
            print("\n" + "="*55)
            print(f"📊 [奥特曼全息看板] 书名：《{book_name}》")
            print(f"📈 整体进度: {progress_bar}")
            print(f"✅ 已完结: {done_ch} 章  (实测: {done_words} 字)")
            print(f"⏳ 待撰写: {left_ch} 章  (预估: {est_left_words} 字)")
            print(f"⏱️ 完本 ETA: {eta_str}")
            print("="*55)
            
            if os.path.exists(file_name):
                print(f"[第{chapter_num}章] ✅ 已完成，跳过...")
                content = read_file(file_name)
                prev_tail = content[-500:] if content else "无"
                continue
            
            content = generate_chapter_robust(chapter_num, line_content, prev_summary, prev_tail, bible)
            chapter_title = line_content.strip()
            final_content = f"第 {chapter_num} 章：{chapter_title}\n\n{content}"
            
            with open(file_name, "w", encoding="utf-8") as f: f.write(final_content)
            CHAPTERS_WRITTEN_SESSION += 1
            prev_tail = content[-500:]
            print(f"    └── 正在更新剧情记忆...", end="\r")
            prev_summary = summarize_chapter(content)
            log(f"✅ 第 {chapter_num} 章完稿！")
            time.sleep(3)

        mark_book_as_finished(folder_path, total_chapters)
        print_brand_end() 

    except KeyboardInterrupt:
        print("\n👋 用户手动停止")
        if 'folder_path' in locals() and folder_path: unlock_book(folder_path)
    except Exception as e:
        print(f"\n❌ 致命错误: {e}")
        if 'folder_path' in locals() and folder_path: unlock_book(folder_path)

if __name__ == "__main__":
    main_writer()