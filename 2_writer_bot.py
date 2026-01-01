import os
import time
import sys
import datetime
import threading
import json
import re
from openai import OpenAI

# ==========================================
#              1. 全局配置区
# ==========================================

CONFIG_FILE = "config_key.json"

# 🔥 模型分级制度 (纯血贵族策略)
TIER_1_NOBLES = [
    "gemini-3-pro-preview",
    "gemini-3-pro-preview-high"
]

TIER_2_KNIGHTS = [
    "gemini-3-pro-preview-low"
]

TIER_3_PEASANTS = [
    "gemini-3-flash-preview"
]

# 高潮关键词 (遇到这些，只准用第一梯队)
CLIMAX_KEYWORDS = [
    "大结局", "终章", "完结", "尾声",
    "决战", "死战", "斩杀", "陨落", "飞升", "成神",
    "高潮", "真相", "觉醒", "屠神", "灭世", "祭天",
    "突破", "进阶", "悟道", "反转", "震惊", "秘境"
]

# 帝王池 (大结局/简介专用)
ULTIMATE_POOL = [
    "gemini-3-pro-preview",
    "gemini-3-pro-preview-high"
]

TIMEOUT_SECONDS = 1200 
client = None
START_WORK_TIME = time.time()
SESSION_START_TIME = time.time() 
CHAPTERS_WRITTEN_SESSION = 0 

# ==========================================
#              2. 基础工具函数
# ==========================================

def set_terminal_title(title):
    sys.stdout.write(f"\x1b]2;{title}\x07")
    sys.stdout.flush()

def print_brand_header():
    print(r"""
    *********************************************************
    * 👑 奥特曼写作引擎 V7.2 (反转·SEO·完整终极版)      *
    * 集成：纯血策略 + 剧情反转 + 自动拟题 + 记忆审计   *
    *********************************************************
    """)

def print_brand_end():
    print(r"""
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
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if len(content) > 100: 
                        finished_chapters += 1
                        finished_words += len(content)
            except: pass 
    remaining_chapters = total_chapters - finished_chapters
    # 动态估算剩余字数
    avg_len = int(finished_words / finished_chapters) if finished_chapters > 0 else 2500
    estimated_remaining_words = remaining_chapters * avg_len
    return finished_chapters, finished_words, remaining_chapters, estimated_remaining_words

def print_final_statistics(folder_path, total_chapters):
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
        print_final_statistics(folder_path, total_chapters)
        unlock_book(folder_path)
        if folder_path.endswith("/"): folder_path = folder_path[:-1]
        base_name = os.path.basename(folder_path)
        dir_name = os.path.dirname(folder_path)
        new_folder_name = f"【已完结】_{base_name}"
        new_full_path = os.path.join(dir_name, new_folder_name)
        os.rename(folder_path, new_full_path)
        print(f"🎉 文件夹已自动封存为: {new_folder_name}")
    except Exception as e:
        print(f"\n⚠️ 完结改名失败: {e}")

# ==========================================
#              3. 修复与回档功能
# ==========================================

def recover_zombie_books():
    print("🚑 正在扫描“假死”书籍（已完结但未生成简介）...")
    count = 0
    for d in os.listdir('.'):
        if not os.path.isdir(d): continue
        if d.startswith("【已完结】"):
            seo_path = os.path.join(d, "发文简介_SEO版.txt")
            if not os.path.exists(seo_path):
                new_name = d.replace("【已完结】_", "")
                if not new_name.startswith("Book_"): new_name = "Book_" + new_name
                try:
                    os.rename(d, new_name)
                    print(f"   🧟‍♂️ 复活书籍: {d} -> {new_name}")
                    count += 1
                except: pass
    if count > 0: print(f"✅ 已成功复活 {count} 本书。\n")
    else: print("✅ 未发现异常书籍。\n")

def rollback_latest_chapter(folder_path):
    chapters_dir = os.path.join(folder_path, "chapters")
    if not os.path.exists(chapters_dir): return
    files = [f for f in os.listdir(chapters_dir) if f.endswith(".txt")]
    max_chap = 0
    max_file = ""
    for f in files:
        match = re.search(r'第(\d+)章', f)
        if match:
            num = int(match.group(1))
            if num > max_chap:
                max_chap = num
                max_file = f
    if max_chap > 0 and max_file:
        full_path = os.path.join(chapters_dir, max_file)
        try:
            os.remove(full_path)
            print(f"⏪ [时光倒流] 已删除最近一章: {max_file} (将执行重写)")
        except: pass

# ==========================================
#              4. 档案与审计系统
# ==========================================

def init_assets_file(folder_path):
    assets_path = f"{folder_path}/assets.txt"
    if not os.path.exists(assets_path):
        initial_state = """
【基础面板】
- 姓名：(待定)
- 境界：凡人
- 当前位置：新手村

【核心资产】
- 灵石/金币：0
- 关键道具：无

【人际关系】
- 仇敌：无
- 盟友：无

【状态栏】
- 身体状况：健康
"""
        with open(assets_path, "w", encoding="utf-8") as f:
            f.write(initial_state.strip())

def extract_money_value(text):
    try:
        match = re.search(r'(灵石|金币|资金|余额)[：:]\s*(\d+)', text)
        if match: return match.group(2)
    except: pass
    return "?"

def update_assets(folder_path, chapter_content):
    assets_path = f"{folder_path}/assets.txt"
    current_assets = read_file(assets_path) or "无"
    old_val = extract_money_value(current_assets)
    
    prompt = f"""
    你是一位严谨的小说档案管理员。
    【上一章档案】：{current_assets}
    【最新章节】：{chapter_content[-4000:]} 
    【任务】：更新面板、资产、人际、状态、时间线。
    【输出格式】：直接输出更新后的完整档案，保持原有Markdown格式。
    """
    
    try:
        # 审计用Flash
        response = client.chat.completions.create(
            model="gemini-3-flash-preview", 
            messages=[{"role": "user", "content": prompt}],
            timeout=60
        )
        new_assets = response.choices[0].message.content
        with open(assets_path, "w", encoding="utf-8") as f:
            f.write(new_assets)
        new_val = extract_money_value(new_assets)
        if old_val != new_val:
            print(f"\n    💰 [账本审计] 资金变化: {old_val} -> {new_val}")
        else:
            print(f"\n    📝 [档案更新] 剧情档案已同步。")
        return True
    except: return False

# ==========================================
#              5. AI 核心生成系统
# ==========================================

def design_twist(chapter_num, outline, prev_summary):
    """🔥 反转设计机 (Flash)"""
    prompt = f"""
    你是网文界的“反转大师”。
    【当前任务】：为第 {chapter_num} 章设计一个精彩的反转或钩子。
    【原细纲】：{outline}
    【前情】：{prev_summary}
    
    请输出【写作指导】：
    1. 读者预期的发展是什么？
    2. 我们要如何打破这个预期（制造反转）？
    3. 结尾如何留悬念（钩子）？
    不要写正文，只给思路，100字以内。
    """
    try:
        response = client.chat.completions.create(
            model="gemini-3-flash-preview",
            messages=[{"role": "user", "content": prompt}],
            timeout=30
        )
        return response.choices[0].message.content
    except:
        return "本章重点制造冲突，结尾留悬念。"

def generate_seo_title(chapter_content, outline_title):
    """🔥 自动拟题机 (Flash)"""
    prompt = f"""
    你是一位标题党大师。
    【任务】：根据正文内容，取一个最吸引眼球、符合SEO优化的章节标题。
    【原细纲标题】：{outline_title}
    【正文摘要】：{chapter_content[:1000]}...
    【要求】：使用“震惊”、“竟然”、“神级”等词，展示核心爽点，10-20字，只输出标题内容。
    """
    try:
        response = client.chat.completions.create(
            model="gemini-3-flash-preview",
            messages=[{"role": "user", "content": prompt}],
            timeout=30
        )
        return response.choices[0].message.content.strip().replace('"', '').replace('标题：', '')
    except:
        return outline_title

def generate_chapter_robust(chapter_num, outline, prev_summary, prev_text_tail, bible, is_final_chapter, assets_data):
    global client
    clean_outline = outline.replace("\n", " ").strip()
    subtitle = clean_outline[:20] + "..." if len(clean_outline) > 20 else clean_outline

    # 1. 构思反转
    print(f"    └── 🎭 正在构思本章反转点...", end="\r")
    twist_instruction = design_twist(chapter_num, clean_outline, prev_summary)

    # 2. 判定高潮 & 模型池
    is_climax = False
    for kw in CLIMAX_KEYWORDS:
        if kw in clean_outline: is_climax = True; break
    if is_final_chapter: is_climax = True

    attempt_queue = []
    attempt_queue.extend(TIER_1_NOBLES) 
    if not is_climax: attempt_queue.extend(TIER_2_KNIGHTS)
    
    print(f"\n🚀 [本章策略] 优先 Pro/High -> Low (禁用Flash)")
    if is_climax: print(f"🔥 [高潮模式] 封锁 Low 模型权限，死磕 Pro！")

    system_prompt = f"""
    你是一位擅长制造“神反转”的白金大神。
    
    【📂 档案数据】：{assets_data}
    
    【🎭 剧情反转指令 (最高优先级)】：{twist_instruction}
    
    【🚫 写作禁令】：
    1. 拒绝流水账，要有波澜。
    2. 期待违背：当读者觉得要赢时让他吃瘪，觉得要输时绝地反击。
    3. 禁止翻译腔、开头自写标题。
    """
    if is_climax:
        system_prompt += "\n🌟【高潮模式】：本章为关键剧情，战斗要剧烈，情感要爆发，文笔要华丽！"

    user_prompt = f"""
    【世界观】：{bible[:1000]}...
    【前情提要】：{prev_summary}
    【上章结尾】：...{prev_text_tail}
    【本章任务】：第 {chapter_num} 章：{outline}
    👉 请开始正文创作（直接写正文）：
    """
    
    while True:
        # 阶段一：尝试贵族模型
        for model_name in attempt_queue:
            stop_heartbeat = threading.Event()
            t = threading.Thread(target=heartbeat, args=(stop_heartbeat, f"{subtitle} | 👑 {model_name}"))
            t.daemon = True
            try:
                log(f"🎬 第 {chapter_num} 章 | 正在调用贵族模型: {model_name}...")
                t.start()
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                    temperature=0.95, presence_penalty=0.6, timeout=TIMEOUT_SECONDS 
                )
                stop_heartbeat.set(); t.join() 
                sys.stdout.write("\r" + " " * 80 + "\r")
                
                content = response.choices[0].message.content
                if content and len(content) >= 1500:
                    log(f"✅ 生成完毕 (字数: {len(content)}) - By {model_name}")
                    return content
                else:
                    log(f"⚠️ 字数不足，切换下一个贵族模型...")
                    continue 
            except KeyboardInterrupt: stop_heartbeat.set(); raise KeyboardInterrupt 
            except Exception as e:
                stop_heartbeat.set(); t.join()
                sys.stdout.write("\r" + " " * 80 + "\r")
                log(f"❌ 贵族模型 {model_name} 报错: {str(e)[:50]}...")
                continue 
        
        # 阶段二：熔断处理
        log("⚠️ 警报：所有 Pro/High/Low 模型均无法响应！")
        if is_climax:
            log("🛑 高潮章节拒绝降级！等待 30 秒冷却后重试 Pro...")
            time.sleep(30); continue 
        
        log("🚑 启用【平民模型 (Flash)】进行熔断救急...")
        for model_name in TIER_3_PEASANTS:
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                    temperature=0.8, timeout=TIMEOUT_SECONDS
                )
                content = response.choices[0].message.content
                log(f"✅ Flash 救急完成 (字数: {len(content)})。")
                return content
            except Exception as e: log(f"❌ Flash 也挂了: {e}")
        
        log("😴 全网瘫痪，冷却 20 秒...")
        time.sleep(20)

def summarize_chapter(content):
    try:
        prompt = f"请用200字总结以下章节的关键剧情：\n\n{content[:2000]}"
        response = client.chat.completions.create(
            model="gemini-3-flash-preview", 
            messages=[{"role": "user", "content": prompt}],
            timeout=60
        )
        return response.choices[0].message.content
    except: return "（摘要生成失败）"

def generate_marketing_intro(folder_path, bible, outline_raw):
    global client
    print("\n" + "="*50)
    log("🔥 正在生成【发文专用·SEO简介】...")
    prompt = f"请阅读这本小说，写一段300字左右的爆款发文简介。素材：{bible[:2000]}"
    while True:
        for model_name in ULTIMATE_POOL:
            try:
                log(f"🎬 正在调用: {model_name} 生成简介...")
                response = client.chat.completions.create(
                    model=model_name, messages=[{"role": "user", "content": prompt}], timeout=120
                )
                intro_content = response.choices[0].message.content
                with open(f"{folder_path}/发文简介_SEO版.txt", "w", encoding="utf-8") as f: f.write(intro_content)
                log(f"✅ 爆款简介已生成。")
                print("="*50 + "\n"); return 
            except Exception as e:
                log(f"❌ {model_name} 失败: {str(e)[:50]}..."); time.sleep(2)
        log("😴 帝王池模型繁忙，冷却 20 秒后重试..."); time.sleep(20)

# ==========================================
#              6. 主程序入口
# ==========================================

def init_client_dynamic():
    global client
    print("\n🔐 --- 身份验证 ---")
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                client = OpenAI(api_key=cfg['api_key'], base_url=cfg['base_url'])
            print("✅ 已自动登录。")
            return
        except: pass

    api_key = input("请输入 API Key: ").strip()
    while not api_key: api_key = input("请输入 API Key: ").strip()
    default_url = "http://172.96.160.216:3000/v1"
    base_url = input(f"Base URL (回车默认 {default_url}): ").strip() or default_url
    client = OpenAI(api_key=api_key, base_url=base_url)
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"api_key": api_key, "base_url": base_url}, f)
    except: pass

def main_writer():
    global CHAPTERS_WRITTEN_SESSION, SESSION_START_TIME
    try:
        print_brand_header()
        recover_zombie_books()
        init_client_dynamic()
        
        all_books = [d for d in os.listdir('.') if os.path.isdir(d) and d.startswith("Book_")]
        all_books.sort(reverse=True)
        if not all_books: print("❌ 没有找到待写书籍！"); return

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
            else: return

        book_name = folder_path.replace("Book_", "").split("_")[-1]
        set_terminal_title(f"🚀 准备中: {book_name}")
        lock_book(folder_path)
        print(f"\n🔒 已锁定项目：{folder_path}")
        rollback_latest_chapter(folder_path)
        init_assets_file(folder_path)
        
        bible = read_file(f"{folder_path}/bible.txt")
        outline_raw = read_file(f"{folder_path}/outline.txt")
        if not bible or not outline_raw:
            print("❌ 资料缺失！请检查 outline.txt 是否为空。"); unlock_book(folder_path); return
            
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
            
            assets_data = read_file(f"{folder_path}/assets.txt")

            if os.path.exists(file_name):
                if os.path.getsize(file_name) > 100: 
                    print(f"[第{chapter_num}章] ✅ 已完成，跳过...")
                    content = read_file(file_name)
                    prev_tail = content[-500:] if content else "无"
                    continue
                else: print(f"[第{chapter_num}章] ⚠️ 检测到文件损坏，准备重写...")
            
            # 1. 生成正文 (带反转)
            is_final = (chapter_num == total_chapters)
            content = generate_chapter_robust(chapter_num, line_content, prev_summary, prev_tail, bible, is_final, assets_data)
            
            # 2. 生成SEO标题
            print(f"    └── 🎣 正在生成爆款SEO标题...", end="\r")
            old_title = line_content.strip()
            seo_title = generate_seo_title(content, old_title)
            print(f"    └── 🎣 标题已优化: {old_title} -> {seo_title}")
            
            # 3. 保存
            final_content = f"第 {chapter_num} 章 {seo_title}\n\n{content}"
            with open(file_name, "w", encoding="utf-8") as f: f.write(final_content)
            
            CHAPTERS_WRITTEN_SESSION += 1
            prev_tail = content[-500:]
            
            # 4. 审计
            print(f"    └── 🤖 正在审计本章资产变化...", end="\r")
            update_assets(folder_path, content)
            
            prev_summary = summarize_chapter(content)
            log(f"✅ 第 {chapter_num} 章完稿！")
            time.sleep(3)

        generate_marketing_intro(folder_path, bible, outline_raw)
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