import os
import time

def print_brand():
    print(r"""
    ****************************************************
    * 🚑 奥特曼旧书档案修复工具 (Archive Fixer)     *
    * Ultraman Airdrop Research Institute       *
    ****************************************************
    """)

def fix_books():
    print_brand()
    
    # 1. 扫描所有书籍
    all_books = [d for d in os.listdir('.') if os.path.isdir(d) and (d.startswith("Book_") or d.startswith("【已完结】"))]
    all_books.sort()
    
    if not all_books:
        print("❌ 未找到任何书籍！")
        return

    print(f"🔍 发现 {len(all_books)} 本书，准备开始修复格式...\n")
    
    total_fixed_files = 0

    for book_folder in all_books:
        print(f"📂 正在扫描: {book_folder}")
        
        # 读取大纲
        outline_path = f"{book_folder}/outline.txt"
        if not os.path.exists(outline_path):
            print(f"   ⚠️ 跳过（缺少大纲文件）")
            continue
            
        with open(outline_path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
            
        chapters_dir = f"{book_folder}/chapters"
        if not os.path.exists(chapters_dir):
            continue
            
        # 遍历所有章节文件
        files = os.listdir(chapters_dir)
        files.sort(key=lambda x: int(x.replace("第", "").replace("章.txt", "")) if "第" in x else 0)
        
        for file_name in files:
            if not file_name.endswith(".txt"): continue
            
            # 解析章节号
            try:
                chapter_num = int(file_name.replace("第", "").replace("章.txt", ""))
            except:
                continue # 文件名格式不对，跳过
            
            # 获取对应的大纲标题
            if chapter_num <= len(lines):
                outline_title = lines[chapter_num-1]
            else:
                outline_title = "未知标题"
                
            file_path = f"{chapters_dir}/{file_name}"
            
            # 读取原始内容
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 检查是否已经修过
            # 这里的判断逻辑是：如果第一行包含 "第 X 章"，说明已经是新格式了
            expected_header = f"第 {chapter_num} 章"
            if content.strip().startswith(expected_header):
                # print(f"   ✅ 第 {chapter_num} 章无需修复")
                continue
            
            # --- 执行修复 ---
            # 构造新内容：标题 + 空两行 + 原文
            new_header = f"第 {chapter_num} 章：{outline_title}"
            new_content = f"{new_header}\n\n{content}"
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
                
            print(f"   ✨ 已修复: 第 {chapter_num} 章 -> 增加标题")
            total_fixed_files += 1

    print("\n" + "="*50)
    print(f"🎉 修复完成！共处理了 {total_fixed_files} 个旧文件。")
    print("现在所有的 TXT 打开都有漂亮的标题了！")
    print("="*50)

if __name__ == "__main__":
    fix_books()