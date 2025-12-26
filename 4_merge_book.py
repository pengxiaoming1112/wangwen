import os
import re
import datetime # 🔥 新增引入

def print_brand():
    print(r"""
    ****************************************************
    * 📦 奥特曼全自动完本打包机 V2.4 (日期智能版)   *
    * Ultraman Airdrop Research Institute       *
    ****************************************************
    """)

def extract_chapter_num(filename):
    match = re.search(r'第(\d+)章', filename)
    if match: return int(match.group(1))
    return 0

def get_sorted_chapters(chapters_dir):
    if not os.path.exists(chapters_dir): return []
    files = [f for f in os.listdir(chapters_dir) if f.endswith(".txt") and not f.startswith(".")]
    files.sort(key=extract_chapter_num)
    return files

def get_real_book_title(folder_path):
    bible_path = f"{folder_path}/bible.txt"
    default_name = os.path.basename(folder_path).replace("Book_", "").replace("【已打包】_", "").replace("【已完结】_", "")
    if not os.path.exists(bible_path): return default_name
    try:
        with open(bible_path, "r", encoding="utf-8") as f:
            for _ in range(5):
                line = f.readline().strip()
                if "书名" in line or "《" in line:
                    clean_title = line.replace("书名", "").replace("：", "").replace(":", "").replace("《", "").replace("》", "").strip()
                    if clean_title: return clean_title
    except: pass
    return default_name

def extract_date_from_folder(folder_name):
    """
    🔥 优化逻辑：如果文件夹名里没有日期，则使用【今天】的日期
    """
    parts = folder_name.split("_")
    for part in parts:
        # 简单的特征识别：8位纯数字
        if part.isdigit() and len(part) == 8: 
            return part
    
    # 如果没找到，返回今天的日期 (例如 20251226)
    return datetime.datetime.now().strftime("%Y%m%d")

def merge_books():
    print_brand()
    
    # 智能过滤：只处理 Book_ 或 【已完结】
    all_books = [d for d in os.listdir('.') if os.path.isdir(d) and (d.startswith("Book_") or d.startswith("【已完结】"))]
    all_books.sort()
    
    pending_books = [d for d in all_books if not d.startswith("【已打包】")]
    
    if not pending_books:
        print("✅ 当前没有需要打包的新书。(已跳过所有【已打包】项目)")
        return

    print(f"🔍 发现 {len(pending_books)} 个新任务，开始打包...\n")
    
    for book_folder in pending_books:
        print(f"-"*60)
        
        real_title = get_real_book_title(book_folder)
        date_str = extract_date_from_folder(book_folder)
        
        print(f"📂 正在处理: {book_folder}")
        print(f"📖 识别真名: 《{real_title}》 | 🗓️ 打包日期: {date_str}")

        chapters_dir = f"{book_folder}/chapters"
        outline_path = f"{book_folder}/outline.txt"
        merged_file_name = f"{date_str}_《{real_title}》_全本.txt"
        merged_file_path = f"{book_folder}/{merged_file_name}"
        
        if not os.path.exists(chapters_dir):
            print(f"   ⚠️ 跳过（资料缺失）")
            continue
            
        outline_lines = []
        if os.path.exists(outline_path):
            with open(outline_path, "r", encoding="utf-8") as f:
                outline_lines = [l.strip() for l in f.readlines() if l.strip()]

        chapter_files = get_sorted_chapters(chapters_dir)
        if not chapter_files:
            print("   ⚠️ 目录为空，跳过")
            continue
            
        full_content = []
        fixed_count = 0
        
        for file_name in chapter_files:
            file_path = f"{chapters_dir}/{file_name}"
            chapter_num = extract_chapter_num(file_name)
            
            with open(file_path, "r", encoding="utf-8") as f: content = f.read()
            
            expected_header_start = f"第 {chapter_num} 章"
            final_chapter_content = ""
            first_line = content.strip().split('\n')[0]
            
            if first_line.startswith(expected_header_start) and ("：" in first_line or ":" in first_line):
                final_chapter_content = content
            else:
                title = "未知章节"
                if 0 < chapter_num <= len(outline_lines): title = outline_lines[chapter_num-1]
                
                lines = content.split('\n')
                if lines[0].strip() == expected_header_start: body = "\n".join(lines[1:]).strip()
                else: body = content.strip()
                
                new_header = f"第 {chapter_num} 章：{title}"
                final_chapter_content = f"{new_header}\n\n{body}"
                with open(file_path, "w", encoding="utf-8") as f: f.write(final_chapter_content)
                fixed_count += 1
            
            full_content.append(final_chapter_content)
            full_content.append("\n\n" + "-"*30 + "\n\n")

        with open(merged_file_path, "w", encoding="utf-8") as f: f.write("".join(full_content))
            
        print(f"   ✅ 打包完成: {merged_file_name}")

        new_folder_name = f"【已打包】_{date_str}_{real_title}"
        if book_folder != new_folder_name:
            if os.path.exists(f"{book_folder}/writing.lock"): os.remove(f"{book_folder}/writing.lock")
            try:
                os.rename(book_folder, new_folder_name)
                print(f"   📦 文件夹归档为: {new_folder_name}")
            except Exception as e:
                print(f"   ⚠️ 改名失败: {e}")

    print("\n" + "="*60)
    print("🎉 所有新书打包完毕！")
    print("="*60)

if __name__ == "__main__":
    merge_books()