#!/bin/bash
# Chrome DevTools MCP 安装脚本

set -e

echo "=========================================="
echo "Chrome DevTools MCP 安装脚本"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查函数
check_command() {
    if command -v "$1" &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 已安装"
        return 0
    else
        echo -e "${YELLOW}✗${NC} $1 未安装"
        return 1
    fi
}

check_version() {
    cmd="$1"
    required="$2"
    current=$($3 2>/dev/null || echo "unknown")

    if [[ "$current" == "unknown" ]]; then
        echo -e "${YELLOW}✗${NC} 无法检测版本"
        return 1
    fi

    echo -e "  当前版本: ${GREEN}$current${NC}"
    echo -e "  要求版本: ${YELLOW}$required+${NC}"

    # 简单版本比较
    if [[ "$current" < "$required" ]]; then
        echo -e "${RED}✗${NC} 版本过低，需要升级"
        return 1
    else
        echo -e "${GREEN}✓${NC} 版本满足要求"
        return 0
    fi
}

# ========================================
# 1. 检查 Node.js
# ========================================
echo "1. 检查 Node.js..."
if check_command node; then
    NODE_VERSION=$(node --version | sed 's/v//')
    NODE_MAJOR=$(echo $NODE_VERSION | cut -d. -f1)

    if [ "$NODE_MAJOR" -lt 20 ]; then
        echo -e "${YELLOW}⚠ Node.js 版本过低 (v$NODE_VERSION)，需要 v20.19.0+${NC}"
        echo ""
        echo "请选择升级方式："
        echo "  1) 使用 NodeSource (推荐)"
        echo "  2) 使用 nvm"
        echo ""
        read -p "选择方式 (1/2) [1]: " choice

        case $choice in
            2)
                echo "使用 nvm 安装 Node.js 20..."
                if ! command -v nvm &> /dev/null; then
                    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
                    export NVM_DIR="$HOME/.nvm"
                    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
                fi
                nvm install 20
                nvm use 20
                ;;
            *)
                echo "使用 NodeSource 安装 Node.js 20..."
                curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
                sudo apt-get install -y nodejs
                ;;
        esac

        echo ""
        echo -e "${GREEN}✓ Node.js 已升级${NC}"
        node --version
    else
        echo -e "${GREEN}✓ Node.js 版本满足要求${NC}"
    fi
else
    echo -e "${RED}✗ Node.js 未安装${NC}"
    echo "正在安装 Node.js 20..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
    echo -e "${GREEN}✓ Node.js 已安装${NC}"
fi

echo ""

# ========================================
# 2. 检查 Chrome
# ========================================
echo "2. 检查 Google Chrome..."
if check_command google-chrome; then
    echo -e "${GREEN}✓ Chrome 已安装${NC}"
    google-chrome --version
elif check_command chromium-browser; then
    echo -e "${GREEN}✓ Chromium 已安装${NC}"
    chromium-browser --version
else
    echo -e "${YELLOW}⚠ Chrome/Chromium 未安装${NC}"
    echo ""
    read -p "是否安装 Google Chrome? (y/n) [y]: " install_chrome

    if [[ "$install_chrome" != "n" ]]; then
        echo "正在下载 Google Chrome..."
        cd /tmp
        wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

        echo "正在安装 Google Chrome..."
        sudo apt-get install -y ./google-chrome-stable_current_amd64.deb
        sudo apt-get -f install -y  # 修复依赖

        rm -f google-chrome-stable_current_amd64.deb
        cd -

        echo -e "${GREEN}✓ Chrome 已安装${NC}"
        google-chrome --version
    else
        echo -e "${YELLOW}跳过 Chrome 安装${NC}"
    fi
fi

echo ""

# ========================================
# 3. 测试 Chrome DevTools MCP
# ========================================
echo "3. 测试 Chrome DevTools MCP..."
echo "运行 npx chrome-devtools-mcp@latest --help..."

if npx -y chrome-devtools-mcp@latest --help > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Chrome DevTools MCP 可用${NC}"
else
    echo -e "${RED}✗ Chrome DevTools MCP 不可用${NC}"
    echo ""
    echo "可能的原因："
    echo "  1. Node.js 版本过低"
    echo "  2. 网络连接问题"
    echo "  3. npm 配置问题"
    echo ""
    echo "建议手动运行以下命令测试："
    echo "  npx -y chrome-devtools-mcp@latest --help"
fi

echo ""

# ========================================
# 4. 创建 MCP 配置
# ========================================
echo "4. 创建 MCP 配置..."

# Claude Code 配置目录
CLAUDE_CONFIG_DIR="$HOME/.config/claude-code"
CLAUDE_CONFIG_FILE="$CLAUDE_CONFIG_DIR/config.json"

mkdir -p "$CLAUDE_CONFIG_DIR"

if [ ! -f "$CLAUDE_CONFIG_FILE" ]; then
    echo "创建 Claude Code 配置文件..."
    cat > "$CLAUDE_CONFIG_FILE" << 'EOF'
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": [
        "-y",
        "chrome-devtools-mcp@latest",
        "--headless=false",
        "--viewport=1280x720"
      ]
    }
  }
}
EOF
    echo -e "${GREEN}✓ Claude Code 配置已创建: $CLAUDE_CONFIG_FILE${NC}"
else
    # 检查是否已有 chrome-devtools 配置
    if grep -q "chrome-devtools" "$CLAUDE_CONFIG_FILE" 2>/dev/null; then
        echo -e "${GREEN}✓ Claude Code 已包含 Chrome DevTools MCP 配置${NC}"
    else
        echo -e "${YELLOW}⚠ Claude Code 配置文件已存在，请手动添加 Chrome DevTools MCP 配置${NC}"
    fi
fi

echo ""

# ========================================
# 5. 显示测试命令
# ========================================
echo "=========================================="
echo "安装完成！"
echo "=========================================="
echo ""
echo "下一步操作："
echo ""
echo "1. 启动 zhineng-bridge 服务："
echo "   cd /home/ai/zhineng-bridge/relay-server"
echo "   python3 start_server.py"
echo ""
echo "2. 运行 E2E 测试："
echo "   pytest tests/e2e/test_chrome_devtools_mcp.py -v"
echo ""
echo "3. 或运行所有 E2E 测试："
echo "   pytest tests/e2e/ -v"
echo ""
echo "4. 使用 Chrome DevTools MCP 进行手动测试："
echo "   在 Claude Code 中执行："
echo "   - 导航到 http://localhost:8000/web/ui/index.html"
echo "   - 截图验证页面"
echo "   - 检查控制台消息"
echo "   - 获取页面快照"
echo ""
