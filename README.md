# wangwen
网文系统
🌟 奥特曼空投研究院·全自动网文矩阵系统 (Ultraman Novel Matrix)
核心代号：pxm_chain

本项目包含两套核心脚本，分别负责“创意策划”与“全自动写作”。支持多开矩阵模式，内置心跳监测与断点续传功能。

⚡️ 懒人速查：常用命令清单
如果你已经配置好环境，直接看这里即可启动：

Bash

# --- 1. 环境准备 (首次运行需要) ---
python3 -m venv venv             # 创建独立虚拟环境 (防止污染系统)
source venv/bin/activate         # 激活环境 (激活后命令行前会有 (venv) 标志)
pip install openai               # 安装核心依赖库

# --- 2. 启动策划端 (生成创意、大纲、文件夹) ---
python3 1_start_project.py       # 启动 Agent 0/1/2，生成设定和大纲

# --- 3. 启动写作端 (挂机自动码字) ---
python3 2_writer_bot.py          # 启动 Agent 3，开始正文写作

# --- 4. 矩阵多开 (在新的终端窗口中) ---
source venv/bin/activate         # ⚠️ 必做：新窗口必须先激活环境
python3 2_writer_bot.py          # 再次运行写作脚本，选择另一本书即可
📖 傻瓜式使用教程 (从零开始)
第一步：环境搭建 (只做一次)
打开你的终端 (Terminal)。

进入项目文件夹：

Bash

cd /你的/项目/路径
激活虚拟环境 (这步最关键！)：

复制并运行：source venv/bin/activate

成功标志：你的命令行最前面出现了一个小括号 (venv)。

安装依赖：

复制并运行：pip install openai

第二步：策划新书 (1_start_project.py)
这是项目的起点，由 Agent 0 (创意)、Agent 1 (架构)、Agent 2 (大纲) 联合工作。

运行命令：

Bash

python3 1_start_project.py
身份验证：

输入你的 API Key。

输入 Base URL (直接回车可使用内置的默认地址)。

输入指令：

输入你想写的标签（例如：历史、赛博修仙、都市神豪）。

Agent 0 会提供 3 个绝妙创意，输入 1-3 选择一个。

等待生成：

系统会自动生成 11万-20万字 的架构规划。

自动创建文件夹（格式如：Book_20251225_回到大明当王爷）。

生成 bible.txt (世界观) 和 outline.txt (细纲)。

第三步：全自动写作 (2_writer_bot.py)
这是真正干活的 Agent 3 (作家)，支持断点续传和风格模仿。

运行命令：

Bash

python3 2_writer_bot.py
选择项目：

程序会自动扫描当前目录下所有的书籍。

输入 auto 自动接管第一本空闲的书，或者输入序号选择。

挂机监控：

程序启动 奥特曼光线引擎，开始逐章写作。

心跳显示：你会看到 ⏳ [奥特曼充能中...] 的提示，每15秒跳动一次，代表 AI 正在思考，不是卡死！

剧情字幕：屏幕会实时显示当前正在写的剧情简介（如：🎬 第5章：『主角一剑破苍穹...』）。

成果验收：

写好的章节会自动保存在 Book_xxx/chapters/ 文件夹内。

全书写完后，屏幕会显示“奥特曼空投研究院”的专属 Logo。

第四步：矩阵多开 (效率翻倍)
想要同时写 5 本书？没问题！

新建一个终端窗口 (Mac 快捷键 Command + T)。

务必先输入：source venv/bin/activate (激活环境)。

运行写作脚本：python3 2_writer_bot.py。

选择另一本状态为 🟢 空闲 的书。

文件锁机制会保证两个窗口不会打架，尽情多开吧！

📂 文件夹结构说明
程序运行后，你的目录会变得井井有条：

Plaintext

Novel_Matrix/
├── 1_start_project.py      # 策划师脚本
├── 2_writer_bot.py         # 作家脚本
├── matrix_db.json          # 创意数据库 (防止生成重复梗)
├── venv/                   # 虚拟环境文件夹
│
├── Book_20251225_书名A/     # --- 书籍 A 项目包 ---
│   ├── bible.txt           # 设定集 (世界观、人设)
│   ├── outline.txt         # 全书细纲
│   ├── writing.lock        # 运行锁 (有这个文件说明正在写)
│   └── chapters/           # --- 正文存放处 ---
│       ├── 第1章.txt
│       ├── 第2章.txt
│       └── ...
│
└── Book_20251225_书名B/     # --- 书籍 B 项目包 ---
    └── ...
❓ 常见问题 (FAQ)
Q: 运行代码提示 ModuleNotFoundError: No module named 'openai'？ A: 你忘记“进屋”了！请先运行 source venv/bin/activate 激活虚拟环境。

Q: 提示 Connection error？ A: 检查你的网络，或者确认你的 Base URL 是否正确（默认地址为 http://172.96.160.216:3000/v1）。

Q: AI 好像卡住了，很久没反应？ A: 只要看到 [奥特曼充能中...] 的秒数在跳动，它就是活着的。长篇小说思考时间较长（有时需要 60-100 秒），请耐心等待。如果超过 20 分钟无反应，程序会自动重启连接。

Q: 字数不够怎么办？ A: 程序内置了质检员，如果生成内容少于 1500 字，会自动打回重写，直到达标为止。

© 2025 奥特曼空投研究院 (Ultraman Airdrop Research Institute) Powered by pxm_chain
