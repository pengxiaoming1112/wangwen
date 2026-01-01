# 🌟 奥特曼空投研究院·网文矩阵系统 (Ultraman Novel Matrix)

📚 奥特曼空投研究院 · AI 网文工业化矩阵系统
(Ultraman Airdrop Research Institute - AI Web Novel Industrial Matrix)

当前版本：

🏛️ 策划架构师：V5.9 (封面炼金术师·终极完整版)

✍️ 核心写作机：V7.3 (题材感知·变色龙版)

这是一个基于 Gemini/OpenAI 模型构建的工业级网文自动化生产流水线。它不仅仅是“写字”，而是具备了总编思维、分卷架构、题材风控、剧情反转以及视觉策划的全能系统。

🌟 核心亮点
1. 🏛️ 策划阶段 (V5.9)
🎩 首席总编定调：自动分析题材（谍战/言情/玄幻），划定“金手指浓度”和“题材红线”，防止内容乱入。

📐 长篇分卷架构：针对 30万+ 字的长篇目标，自动拆分为“卷一、卷二...”，每卷都有独立的地图和高潮，拒绝中期崩盘。

📥 多行灵感捕获：支持粘贴超长故事梗概（带空行），完美还原用户脑洞。

💅 SEO 爆款标题：自动将文青标题整形为“流量收割机”式的网文标题。

🎨 封面炼金术师：自动生成 Midjourney 和 Stable Diffusion 的英文提示词，精准把控封面视觉。

2. ✍️ 写作阶段 (V7.3)
👑 纯血贵族策略：死磕 Pro 和 High 级模型，拒绝流水账。只有在 API 全挂时才短暂降级。

🦎 题材变色龙：启动时自动感知文风。谍战文冷峻严谨，言情文细腻拉扯，自动屏蔽违和词汇（如古代出现手机）。

🎭 剧情反转机：写正文前先构思“钩子”和“反转”，打破读者预期。

💰 动态资产审计：不只是记灵石！根据题材自动审计“情报/弹药/好感度/人脉”等核心资源。

🎣 自动拟题机：写完正文后，根据内容自动生成最具吸引力的章节标题。


3. 🚑 档案修复师 (3_fix_titles.py)
功能：旧书拯救工具。
用途：如果你有早期生成的 TXT 缺失标题或格式混乱，运行此脚本可一键根据大纲修复所有章节头。
4. 📦 智能打包机 (4_merge_book.py)
功能：负责完本后的校对、合并、归档。
V2.4 特性：
真名觉醒：直接读取 bible.txt 获取书籍真名，修正文件夹命名。
智能过滤：自动跳过已打包 (【已打包】_) 的项目，只处理新书。
完美排序：解决 1, 10, 2 的乱序问题，合并生成 日期_《书名》_全本.txt。



🛠️ 快速开始 (Installation)
1. 环境准备 (MacOS/Linux)
确保你已经安装了 Python 3。

Bash

# 1. 进入项目目录
cd /你的项目路径/

# 2. 创建虚拟环境 (隔离系统环境，防止报错)
python3 -m venv venv

# 3. 激活虚拟环境
source venv/bin/activate

# 4. 安装依赖库
python3 -m pip install openai
2. 首次配置
系统内置了 自动免登 (Auto-Login) 功能。

首次运行脚本时，输入一次 API Key 和 Base URL。

程序会自动生成 config_key.json，下次启动无需再输。

注意：如果 API 连接失败，程序会自动删除配置文件并要求重输。

🚀 工作流 (Workflow)
第一步：大纲策划 (The Architect)
运行脚本 1，生成从创意到细纲的全套资料。

Bash

python3 1_start_project.py
交互：输入题材标签 -> 粘贴灵感(按#结束) -> 设定字数。

产出：

idea.txt：核心创意与卖点。

bible.txt：世界观、分卷宏观大纲、总编定调书。

outline.txt：全书分章细纲。

封面提示词_AI绘画版.txt：直接复制去画图。

第二步：正文写作 (The Writer)
运行脚本 2，开始全自动写作。

Bash

python3 2_writer_bot.py
交互：选择要写的项目（支持断点续写）。

功能：

自动读取 assets.txt 进行资产审计。

实时显示进度条、预计完本时间 (ETA)。

写完后自动生成《发文简介_SEO版.txt》。

完本后自动打包归档。

第三步：合并打包 (The Packager)
(可选) 将所有章节合并为一个 txt 文件，方便上传。

Bash

python3 4_merge_book.py
📂 目录结构说明
Plaintext

Project_Root/
├── 1_start_project.py    # [策划] 众神殿 V5.9
├── 2_writer_bot.py       # [写作] 写作引擎 V7.3
├── 4_merge_book.py       # [工具] 合并脚本
├── config_key.json       # [配置] 自动生成的密钥文件
├── venv/                 # [环境] 虚拟环境文件夹
└── Book_大幽缝尸人/       # [项目] 自动生成的书籍文件夹
    ├── idea.txt          # 创意源文件
    ├── bible.txt         # 世界观与宏观设定
    ├── outline.txt       # 详细细纲
    ├── assets.txt        # 动态资产档案 (自动更新)
    ├── 封面提示词...txt   # AI绘画提示词
    ├── writing.lock      # 写作锁 (防止多开)
    └── chapters/         # 章节目录
        ├── 第1章 震惊！开局缝合妖魔.txt
        ├── 第2章 ...
        └── ...
⚠️ 常见问题
报错 ModuleNotFoundError: No module named 'openai'

原因：未进入虚拟环境。

解决：执行 source venv/bin/activate。

报错 externally-managed-environment

原因：试图在系统全局安装包。

解决：请务必使用虚拟环境，并使用 python3 -m pip install openai 安装。

写作脚本卡住不动了？

不要慌，脚本正在进行“死磕重试”。只要控制台显示 🧊 API冷却...，说明它在等待服务器恢复，不会丢稿。

祝你新书大火，日更百万！🚀

### 第一步：初始化环境
```bash
# 1. 进入目录
cd ~/Local_Projects/Novel_Matrix

# 2. 激活奥特曼虚拟环境 (必须!)
python3 -m venv venv
source venv/bin/activate

# 3. 安装依赖 (仅首次)
pip install openai

-------------

如果出错：🛠️ 彻底修复步骤
1. 退出当前的异常环境

Bash

deactivate
(如果提示 command not found 也没关系，继续下一步)

2. 删掉旧的、坏掉的虚拟环境文件夹

Bash

rm -rf venv
3. 创建一个全新的虚拟环境

Bash

python3 -m venv venv
4. 激活新环境

Bash

source venv/bin/activate
5. 重新安装 openai 包

Bash

pip install openai
✅ 验证是否修好
等上面第 5 步跑完（看到 Successfully installed...），你再运行脚本：
