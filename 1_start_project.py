import os
import time
import random
import json
import threading
import datetime
import sys
import re
from openai import OpenAI

# ==========================================
#              1. 全局配置区
# ==========================================

# 🔥 策划阶段：双核顶配轮换
MODEL_POOL = [
    "gemini-3-pro-preview",
    "gemini-3-pro-preview-high"
]
TIMEOUT_SECONDS = 600
client = None

# ==========================================
#              2. 基础工具函数
# ==========================================

def print_brand_header():
    print(r"""
    *********************************************************
    * 🏛️ 奥特曼众神殿 V6.0 (验证·防呆最终版)            *
    * 自动检测Key有效性 | 连接失败自动重输 | 全功能集成     *
    *********************************************************
    """)

def print_brand_end():
    print("\n✨ 策划全流程结束！大纲、细纲、封面提示词均已生成。")

def log(msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")

def heartbeat(stop_event, task_name):
    start_wait = time.time()
    while not stop_event.is_set():
        time.sleep(1)
        elapsed = int(time.time() - start_wait)
        if elapsed > 0 and elapsed % 2 == 0: 
            spinner = ["|", "/", "-", "\\"][elapsed % 4]
            sys.stdout.write(f"\r{spinner} [Pro级大脑思考中...] {task_name} 已进行 {elapsed} 秒...   ")
            sys.stdout.flush()

def cool_down_timer(seconds, reason="API冷却"):
    for i in range(seconds, 0, -1):
        sys.stdout.write(f"\r🧊 {reason}: {i}秒...   ")
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write("\r" + " " * 60 + "\r")

def sanitize_filename(name):
    return "".join([c for c in name if c.isalnum() or c in (' ', '_', '-') or '\u4e00' <= c <= '\u9fa5']).strip()

def create_project_folder(book_title):
    clean_title = sanitize_filename(book_title)
    if not clean_title: clean_title = "新书项目"
    if len(clean_title) > 30: clean_title = clean_title[:30]
    
    target_name = f"Book_{clean_title}"
    if os.path.exists(target_name):
        timestamp = time.strftime("%Y%m%d_%H%M")
        target_name = f"Book_{timestamp}_{clean_title}"
    if not os.path.exists(target_name):
        os.makedirs(target_name)
        os.makedirs(f"{target_name}/chapters")
    return target_name

def call_ai_infinite(system_prompt, user_prompt, task_name="计算中"):
    global client
    attempt = 0
    while True:
        attempt += 1
        for model_name in MODEL_POOL:
            stop_heartbeat = threading.Event()
            t = threading.Thread(target=heartbeat, args=(stop_heartbeat, f"{task_name} (第{attempt}轮 | {model_name})"))
            t.daemon = True
            try:
                t.start() 
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                    timeout=TIMEOUT_SECONDS
                )
                stop_heartbeat.set()
                if t.is_alive(): t.join()
                sys.stdout.write("\r" + " " * 80 + "\r")
                content = response.choices[0].message.content
                if content: return content
            except Exception as e:
                stop_heartbeat.set()
                if t.is_alive(): t.join()
                sys.stdout.write("\r" + " " * 80 + "\r")
                continue 
        log(f"🛑 暂时繁忙，冷却 20 秒后重试...")
        cool_down_timer(20, "等待恢复")

# 🔥 多行输入工具 (使用 # 号结束)
def get_multiline_input(prompt_text):
    print(f"{prompt_text}")
    print("   👉 请直接粘贴文本。输入完毕后，在【新的一行】输入 '#' 然后回车确认:")
    lines = []
    while True:
        try:
            line = input()
            if line.strip() == '#':
                break
            lines.append(line)
        except EOFError:
            break
    return "\n".join(lines)

# ==========================================
#              3. 🔥 核心修复：智能身份验证
# ==========================================

def init_client_dynamic():
    global client
    print("\n🔐 --- 身份验证 ---")
    
    # 循环直到获取一个有效的 Client
    while True:
        api_key = ""
        base_url = ""
        
        # 1. 尝试读取本地缓存
        if os.path.exists("config_key.json"):
            try:
                with open("config_key.json", "r") as f:
                    cfg = json.load(f)
                    api_key = cfg.get('api_key', "")
                    base_url = cfg.get('base_url', "")
                print(f"👀 检测到本地配置文件，正在尝试连接服务器...")
            except:
                print("⚠️ 配置文件格式错误，准备重新输入。")
        
        # 2. 如果没有缓存，或者缓存被删了，要求输入
        if not api_key:
            api_key = input("请输入 API Key: ").strip()
            while not api_key: api_key = input("请输入 API Key: ").strip()
            
            default_url = "http://172.96.160.216:3000/v1"
            base_url = input(f"Base URL (回车默认 {default_url}): ").strip() or default_url

        # 3. 🔥 关键步骤：当场测试连接！
        try:
            # 创建临时客户端
            temp_client = OpenAI(api_key=api_key, base_url=base_url)
            
            # 发送一个极小的探测包 (列出模型) 来验证 Key 是否有效
            # 如果 Key 错误或网络不通，这里会直接报错，跳到 except
            temp_client.models.list() 
            
            # 如果没报错，说明连接成功！
            client = temp_client
            print("✅ 验证成功！连接已建立。")
            
            # 保存正确的配置
            with open("config_key.json", "w") as f:
                json.dump({"api_key": api_key, "base_url": base_url}, f)
            
            # 退出循环，进入主程序
            return 
            
        except Exception as e:
            print(f"\n❌ 连接失败: {str(e)[:100]}...")
            print("⚠️ 警告：当前的 API Key 或 URL 无效！")
            
            # 🔥 自动删除错误的配置文件，确保下次循环不会再读它
            if os.path.exists("config_key.json"):
                os.remove("config_key.json")
                print("🗑️ 已自动删除无效的配置文件。")
            
            print("🔄 请重新输入正确的配置...\n")
            # 循环回到开头，强制用户重输

# ==========================================
#              4. 首席总编 & 标题专家
# ==========================================

def consult_chief_editor(tag, user_input):
    print(f"\n🎩 正在召开总编选题会，判定题材基调 (Tag: {tag})...")
    
    prompt = f"""
    你是一位资深的网文总编。
    【用户输入】：题材-{tag} | 灵感-{user_input}
    
    请制定《新书基调白皮书》，界定三点：
    1. **【金手指浓度】**：玄幻/快穿必须有强系统；谍战/言情/现实严禁系统。
    2. **【核心看点】**：爽文看升级，言情看拉扯，悬疑看反转。
    3. **【差异化切入】**：提供5个独特切入点防止同质化。
    
    【输出格式】：
    JSON: {{ "cheat_level": "...", "cheat_desc": "...", "core_hook": "...", "variations": ["..."], "forbidden_elements": "..." }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gemini-3-pro-preview", 
            messages=[{"role": "user", "content": prompt}],
            timeout=60
        )
        content = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        json_str = re.search(r'\{.*\}', content, re.DOTALL).group(0)
        data = json.loads(json_str)
        print(f"📋 总编定调：{data['cheat_level']} | 禁区：{data['forbidden_elements']}")
        return data
    except Exception as e:
        print(f"⚠️ 总编缺席，使用默认配置。")
        return {"cheat_level": "Medium", "cheat_desc": "默认", "core_hook": "常规", "variations": ["复仇"], "forbidden_elements": "无"}

def polish_killer_title(draft_title, draft_logline, tag, config_data):
    print(f"\n💅 正在进行 SEO 标题整形 (原名: {draft_title})...")
    
    prompt = f"""
    你是一位网文界的“起名大师”和SEO专家。
    【当前草案】：{draft_title}
    【梗概】：{draft_logline}
    【题材】：{tag}
    【金手指设定】：{config_data['cheat_level']} ({config_data['cheat_desc']})
    
    【任务】：请重新取一个**极具吸引力、符合SEO搜索习惯**的爆款书名。
    
    【起名公式】：
    1. **爽文**：[强金手指] + [身份] + [爽点]。例：《长生：从给功法杀毒开始》。
    2. **正剧/玄幻**：[宏大意象] + [独特设定]。例：《诡秘之主》。
    3. **言情/虐文**：[唯美/反差] + [CP关系]。例：《将门毒后》、《偷偷藏不住》。
    4. **悬疑/脑洞**：[核心矛盾/诡异点]。
    
    请生成 1 个最好的书名，**只输出书名，不要书名号**。
    """
    try:
        new_title = call_ai_infinite(prompt, "请给出一个最炸裂的书名。", task_name="标题优化")
        clean_title = new_title.replace("《", "").replace("》", "").replace("书名：", "").strip()
        print(f"✨ 标题整形成功：{draft_title}  --->  {clean_title}")
        return clean_title
    except: return draft_title

# ==========================================
#              5. 封面炼金术师
# ==========================================

def generate_art_prompt(folder_path, title, logline, tag, config_data):
    print(f"\n🎨 正在炼制封面视觉符号 (Cover Alchemist)...")
    
    prompt = f"""
    你是一位顶级的 AI 绘画提示词专家（精通 Midjourney V6 和 Stable Diffusion）。
    
    【书籍信息】：
    - 书名：{title}
    - 题材：{tag}
    - 核心梗概：{logline}
    - 风格基调：{config_data.get('cheat_desc', '常规')}
    - 禁忌：{config_data.get('forbidden_elements', '无')}
    
    【任务】：提炼 1 个最核心的“视觉符号”，并生成 MJ 和 SD 的提示词。
    **构图要求**：必须留出顶部 1/3 的空白区域（Top 1/3 negative space）。
    
    【输出格式】：
    JSON: 
    {{
        "visual_concept": "中文描述",
        "mj_prompt": "英文 MJ Prompt",
        "sd_prompt": "英文 SD Positive",
        "sd_negative": "英文 SD Negative"
    }}
    """
    
    try:
        res = call_ai_infinite(prompt, "请生成封面提示词", task_name="封面设计")
        content = res.replace("```json", "").replace("```", "").strip()
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            file_content = f"""
【书籍封面设计方案】
书名：{title}
题材：{tag}

---------------------------------------------------
1. 核心视觉概念 (Visual Concept)
---------------------------------------------------
{data['visual_concept']}

---------------------------------------------------
2. Midjourney 专用提示词 (直接复制)
---------------------------------------------------
{data['mj_prompt']} --ar 2:3 --stylize 250

---------------------------------------------------
3. Stable Diffusion 专用提示词
---------------------------------------------------
[Positive]:
{data['sd_prompt']}

[Negative]:
{data['sd_negative']}
            """
            with open(f"{folder_path}/封面提示词_AI绘画版.txt", "w", encoding="utf-8") as f:
                f.write(file_content.strip())
            print(f"✅ 封面提示词已生成。")
            return data
    except Exception as e:
        print(f"⚠️ 封面提示词生成失败: {e}")
        return None

# ==========================================
#              6. 智能 Agent (策划)
# ==========================================

def agent0_meeting(tag, user_input, round_num, config_data):
    random_direction = random.choice(config_data['variations'])
    custom_instruction = f"用户灵感(必须完整包含):\n'''{user_input}'''" if user_input else "自由发挥"

    system_prompt = f"""
    你是一位顶级网文策划。请构思一个创意。
    【总编要求】：
    1. 金手指：{config_data['cheat_level']} - {config_data['cheat_desc']}
    2. 禁忌：{config_data['forbidden_elements']}
    3. 切入点：**{random_direction}**
    
    {custom_instruction}
    
    **重要**：如果用户提供了灵感故事，请务必将其作为核心背景。
    
    【输出格式】：
    JSON: {{ "title": "草拟书名", "logline": "一句话梗概", "highlight": "核心卖点" }}
    """
    
    res = call_ai_infinite(system_prompt, f"请针对标签“{tag}”进行策划。", task_name=f"第{round_num}场脑暴")
    if res:
        try:
            clean_res = res.replace("```json", "").replace("```", "").strip()
            match = re.search(r'\{.*\}', clean_res, re.DOTALL)
            if match: return json.loads(match.group(0))
        except: pass
    return None

def agent1_macro_structure_volumes(idea_summary, total_words, config_data):
    """🔥 分卷宏观规划器"""
    num_volumes = 3
    if total_words > 500000: num_volumes = 5
    elif total_words < 150000: num_volumes = 2
    
    print(f"\n📐 正在构建分卷架构 (目标: {total_words}字 / 约{int(total_words/2500)}章 / 分{num_volumes}卷)...")
    
    prompt = f"""
    你是一位擅长长篇布局的网文大神。
    【任务】：为一部 {total_words} 字的长篇小说规划【分卷大纲】。
    
    【核心创意】：{idea_summary}
    【风控限制】：{config_data['forbidden_elements']}
    
    请严格按照 {num_volumes} 卷进行规划。
    每一卷都要有：卷名、核心地图、主要矛盾、高潮事件、预估章节数。
    
    输出格式要求：清晰的分卷列表。
    """
    return call_ai_infinite(prompt, "请输出分卷宏观大纲。", task_name="分卷规划")

def agent2_outline_detailed_volumes(macro_structure, total_chapters):
    print(f"\n🧱 正在填充 {total_chapters} 章的详细细纲 (分卷填充)...")
    prompt = f"""
    你是一位主编。请根据【分卷宏观大纲】生成全书细纲。
    【分卷大纲】：
    {macro_structure}
    
    【任务要求】：
    1. 总共生成约 {total_chapters} 章。
    2. **严格按照分卷节奏**。
    3. **每章要有钩子**。
    4. **输出格式**：
       纯文本列表，每一行只写一章。
       不要写"第一卷"这种大标题，直接输出章节列表。
    """
    return call_ai_infinite(prompt, "开始生成全书细纲。", task_name="生成细纲")

# ==========================================
#              7. 主程序入口
# ==========================================

def start_new_project():
    print_brand_header()
    
    # 🔥 1. 带验证的初始化
    init_client_dynamic()
    
    tag = input("\n📝 1. 题材标签 (如 宫斗/谍战/玄幻): ").strip() or "玄幻"
    
    # 🔥 2. 灵感录入 (带 # 号结束符)
    user_input = get_multiline_input("\n💡 2. 灵感片段录入")
    
    # 🔥 3. 询问字数目标
    word_count_input = input("\n📏 3. 目标字数 (万字, 默认30): ").strip()
    total_words = int(word_count_input) * 10000 if word_count_input.isdigit() else 300000
    total_chapters = int(total_words / 2500)
    print(f"   ⚙️  目标设定: {total_words} 字 | 约 {total_chapters} 章")

    # 1. 总编定调
    config_data = consult_chief_editor(tag, user_input)
    
    # 2. 脑暴
    candidates = []
    print(f"\n🧠 正在进行合规化脑暴...")
    
    while len(candidates) < 3:
        idx = len(candidates) + 1
        idea = agent0_meeting(tag, user_input, idx, config_data)
        if idea:
            candidates.append(idea)
            print(f"✅ 方案[{idx}]《{idea['title']}》\n   🔥 {idea['logline'][:50]}...")

    print("\n🏆 --- 请选择最佳创意 ---")
    for i, cand in enumerate(candidates):
        print(f"[{i+1}] 《{cand['title']}》\n    📝 {cand['logline']}\n")
    
    idx = -1
    while True:
        choice = input("👉 请输入序号 (1-3): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(candidates):
            idx = int(choice) - 1
            print(f"✅ 你选择了方案 [{choice}]")
            break
        else:
            print("❌ 输入无效！请输入 1、2 或 3，不要直接回车。")
            
    final_idea_obj = candidates[idx]
    
    # 3. 标题整形
    killer_title = polish_killer_title(final_idea_obj['title'], final_idea_obj['logline'], tag, config_data)
    final_idea_obj['title'] = killer_title 
    
    # 4. 创建文件夹
    folder_path = create_project_folder(final_idea_obj['title'])
    print(f"\n📂 项目文件夹已创建: {folder_path}")
    
    final_idea_str = f"书名：《{final_idea_obj['title']}》\n梗概：{final_idea_obj['logline']}\n卖点：{final_idea_obj['highlight']}"
    with open(f"{folder_path}/idea.txt", "w", encoding="utf-8") as f: f.write(final_idea_str)
    
    # 🔥 5. 宏观规划 (分卷)
    macro = agent1_macro_structure_volumes(final_idea_str, total_words, config_data)
    with open(f"{folder_path}/bible.txt", "w", encoding="utf-8") as f: f.write(macro)
    
    # 🔥 6. 细纲填充
    outline = agent2_outline_detailed_volumes(macro, total_chapters)
    with open(f"{folder_path}/outline.txt", "w", encoding="utf-8") as f: f.write(outline)
    
    # 🔥 7. 生成封面提示词
    generate_art_prompt(folder_path, killer_title, final_idea_obj['logline'], tag, config_data)
    
    print_brand_end()

if __name__ == "__main__":
    start_new_project()