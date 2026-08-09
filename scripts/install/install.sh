#!/bin/bash
# 系统依赖安装脚本

set -e

echo "==================================="
echo "知识脉络分析系统 - 依赖安装"
echo "==================================="

# 检测操作系统
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
else
    OS="unknown"
fi

echo ""
echo "检测到操作系统: $OS"

# 安装系统依赖
echo ""
echo "==================================="
echo "安装系统依赖"
echo "==================================="

if [ "$OS" == "linux" ]; then
    echo "在 Linux 上安装系统依赖..."

    # 更新包管理器
    sudo apt-get update

    # 安装 ffmpeg（音视频处理）
    echo "安装 ffmpeg..."
    sudo apt-get install -y ffmpeg

    # 安装 Redis
    echo "安装 Redis..."
    sudo apt-get install -y redis-server

    # 启动 Redis
    sudo systemctl start redis-server
    sudo systemctl enable redis-server

    echo "✓ Linux 系统依赖安装完成"

elif [ "$OS" == "macos" ]; then
    echo "在 macOS 上安装系统依赖..."

    # 检查 Homebrew
    if ! command -v brew &> /dev/null; then
        echo "Homebrew 未安装，正在安装..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi

    # 安装 ffmpeg
    echo "安装 ffmpeg..."
    brew install ffmpeg

    # 安装 Redis
    echo "安装 Redis..."
    brew install redis

    # 启动 Redis
    brew services start redis

    echo "✓ macOS 系统依赖安装完成"

else
    echo "⚠ 未知操作系统，请手动安装以下依赖:"
    echo "  - ffmpeg"
    echo "  - Redis"
fi

# 安装 Neo4j
echo ""
echo "==================================="
echo "安装 Neo4j"
echo "==================================="

read -p "是否安装 Neo4j? (y/n): " install_neo4j

if [ "$install_neo4j" == "y" ]; then
    if [ "$OS" == "linux" ]; then
        echo "在 Linux 上安装 Neo4j..."

        # 添加 Neo4j 仓库
        wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
        echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list
        sudo apt-get update

        # 安装 Neo4j
        sudo apt-get install -y neo4j

        # 启动 Neo4j
        sudo systemctl start neo4j
        sudo systemctl enable neo4j

        echo "✓ Neo4j 安装完成"
        echo "  访问 http://localhost:7474 设置密码"

    elif [ "$OS" == "macos" ]; then
        echo "在 macOS 上安装 Neo4j..."

        brew install neo4j

        echo "✓ Neo4j 安装完成"
        echo "  运行 'neo4j start' 启动服务"
        echo "  访问 http://localhost:7474 设置密码"
    fi
else
    echo "跳过 Neo4j 安装"
    echo "注意: 知识图谱功能将无法使用"
fi

# Python 依赖
echo ""
echo "==================================="
echo "安装 Python 依赖"
echo "==================================="

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python 版本: $python_version"

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 升级 pip
echo "升级 pip..."
pip install --upgrade pip

# 安装 PyTorch（根据系统选择版本）
echo ""
echo "安装 PyTorch..."
read -p "是否有可用的 GPU? (y/n): " has_gpu

if [ "$has_gpu" == "y" ]; then
    echo "安装 GPU 版本的 PyTorch..."
    pip install torch torchvision torchaudio
else
    echo "安装 CPU 版本的 PyTorch..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

# 安装其他依赖
echo ""
echo "安装其他 Python 依赖..."
pip install -r requirements.txt

echo "✓ Python 依赖安装完成"

# 下载 NLP 模型
echo ""
echo "==================================="
echo "下载 NLP 模型"
echo "==================================="

read -p "是否现在下载 NLP 模型? (需要较长时间和网络) (y/n): " download_models

if [ "$download_models" == "y" ]; then
    echo "下载 sentence-transformers 模型..."
    python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"

    echo "下载 HanLP 模型..."
    python3 -c "import hanlp; hanlp.load(hanlp.pretrained.mtl.CLOSE_TOK_POS_NER_SRL_DEP_SDP_CON_ELECTRA_BASE_ZH)"

    echo "下载 Whisper 模型..."
    python3 -c "import whisper; whisper.load_model('base')"

    echo "✓ NLP 模型下载完成"
else
    echo "跳过模型下载"
    echo "注意: 首次运行时会自动下载模型"
fi

# 创建必要的目录
echo ""
echo "==================================="
echo "创建数据目录"
echo "==================================="

mkdir -p data/uploads
mkdir -p data/processed
mkdir -p data/audio_extracts
mkdir -p data/chromadb
mkdir -p data/reports
mkdir -p logs

echo "✓ 目录创建完成"

# 配置环境变量
echo ""
echo "==================================="
echo "配置环境变量"
echo "==================================="

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✓ 已创建 .env 文件"
    echo "  请编辑 .env 文件配置数据库连接等信息"
else
    echo ".env 文件已存在"
fi

# 安装完成
echo ""
echo "==================================="
echo "安装完成！"
echo "==================================="

echo ""
echo "后续步骤:"
echo "1. 编辑 .env 文件，配置数据库连接"
echo "2. 如果安装了 Neo4j，访问 http://localhost:7474 设置密码"
echo "3. 运行 './start.sh' 启动系统"
echo "4. 运行 'python3 test_system.py' 测试系统功能"

echo ""
echo "服务地址:"
echo "  - API 文档: http://localhost:8000/docs"
echo "  - Neo4j 控制台: http://localhost:7474"
echo "  - Redis 端口: 6379"

echo ""
echo "有用的命令:"
echo "  - 启动系统: ./start.sh"
echo "  - 初始化数据库: python3 init_db.py"
echo "  - 运行测试: python3 test_system.py"
echo "  - 启动 Celery Worker: celery -A app.tasks worker --loglevel=info"

echo ""
