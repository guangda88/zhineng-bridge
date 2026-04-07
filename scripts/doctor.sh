#!/usr/bin/env bash
# ============================================================================
# 智桥环境诊断脚本 (doctor.sh)
# 用法: bash scripts/doctor.sh
# ============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

pass=0
fail=0
warn=0

ok()   { echo -e "  ${GREEN}✅ $1${NC}"; pass=$((pass+1)); }
no()   { echo -e "  ${RED}❌ $1${NC}"; fail=$((fail+1)); }
maybe(){ echo -e "  ${YELLOW}⚠️  $1${NC}"; warn=$((warn+1)); }

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo ""
echo -e "${CYAN}=== 智桥环境诊断 ===${NC}"
echo "项目: $PROJECT_ROOT"
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# ── 1. Python 环境 ─────────────────────────────────────────────────────────
echo -e "${CYAN}[1/10] Python 环境${NC}"

if command -v python3 >/dev/null 2>&1; then
    PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")')
    PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
    PY_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
    if [ "$PY_MAJOR" -gt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -ge 8 ]; }; then
        ok "Python $PY_VERSION (>= 3.8)"
    else
        no "Python $PY_VERSION 版本过低，需要 >= 3.8"
    fi
else
    no "未找到 python3 命令"
fi

# ── 2. Python 依赖 ────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}[2/10] Python 依赖${NC}"

for pkg in websockets aiohttp structlog pydantic pydantic_settings; do
    DISPLAY="${pkg}"
    IMPORT="${pkg}"
    # pydantic_settings 模块名带横线时用下划线导入
    if [ "$pkg" = "pydantic_settings" ]; then
        DISPLAY="pydantic-settings"
    fi
    if python3 -c "import ${IMPORT}" 2>/dev/null; then
        VER=$(python3 -c "import ${IMPORT}; print(${IMPORT}.__version__)" 2>/dev/null || echo "ok")
        ok "${DISPLAY} ($VER)"
    else
        no "${DISPLAY} 未安装 → pip install ${DISPLAY}"
    fi
done

# ── 3. 端口可用性 ─────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}[3/10] 端口可用性${NC}"

check_port() {
    local port="$1"
    local name="$2"
    if ss -tlnp 2>/dev/null | grep -q ":${port} " || netstat -tlnp 2>/dev/null | grep -q ":${port} "; then
        maybe "端口 $port ($name) 已被占用"
    else
        ok "端口 $port ($name) 可用"
    fi
}

check_port 8765 "WebSocket"
check_port 8080 "HTTP API"

# ── 4. 核心文件 ────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}[4/10] 核心文件${NC}"

for f in \
    VERSION \
    relay-server/server.py \
    relay-server/http_server.py \
    relay-server/auth_db.py \
    relay-server/plugin_system.py \
    relay-server/start_server.py \
    phase1/session_manager/session_manager.py \
    phase1/session_manager/start_manager.py \
    web/ui/index.html \
    web/ui/js/client.js; do
    if [ -f "$PROJECT_ROOT/$f" ]; then
        ok "$f"
    else
        no "$f 文件缺失"
    fi
done

# ── 5. 目录结构 ────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}[5/10] 目录结构${NC}"

for d in relay-server phase1/session_manager web/ui web/ui/js web/ui/css; do
    if [ -d "$PROJECT_ROOT/$d" ]; then
        ok "$d/"
    else
        no "$d/ 目录缺失"
    fi
done

# ── 6. 数据库文件 ──────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}[6/10] 数据库文件${NC}"

DB_FILE="$PROJECT_ROOT/relay-server/data/users.db"
if [ -f "$DB_FILE" ]; then
    SIZE=$(du -h "$DB_FILE" | cut -f1)
    ok "数据库文件存在 ($SIZE)"
else
    maybe "数据库文件不存在 (首次启动时自动创建)"
fi

DB_DIR=$(dirname "$DB_FILE")
if [ -d "$DB_DIR" ]; then
    ok "数据库目录存在"
else
    maybe "数据库目录不存在，首次启动时自动创建"
fi

# ── 7. 服务状态 ────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}[7/10] 服务状态${NC}"

# WebSocket 服务检查
if python3 -c "
import asyncio, websockets, json
async def ping():
    try:
        async with websockets.connect('ws://localhost:8765', close_timeout=3) as ws:
            await ws.send(json.dumps({'type': 'ping'}))
            resp = await asyncio.wait_for(ws.recv(), timeout=3)
            data = json.loads(resp)
            if data.get('type') == 'pong':
                print('ok')
            else:
                print('wrong_response')
    except Exception as e:
        print(f'fail:{e}')
asyncio.run(ping())
" 2>/dev/null | grep -q "ok"; then
    ok "WebSocket 服务响应正常 (ws://localhost:8765)"
else
    maybe "WebSocket 服务未运行或无法连接 (ws://localhost:8765)"
fi

# HTTP 健康检查
if command -v python3 >/dev/null 2>&1; then
    HTTP_STATUS=$(python3 -c "
import urllib.request, urllib.error
try:
    req = urllib.request.Request('http://localhost:8080/health')
    resp = urllib.request.urlopen(req, timeout=3)
    print(resp.status)
except urllib.error.HTTPError as e:
    print(e.code)
except Exception:
    print('fail')
" 2>/dev/null)
    if [ "$HTTP_STATUS" = "200" ]; then
        ok "HTTP 健康检查通过 (http://localhost:8080/health)"
    elif [ "$HTTP_STATUS" = "503" ]; then
        maybe "HTTP 健康检查返回 503 (服务降级)"
    else
        maybe "HTTP 服务未运行或无法连接 (http://localhost:8080/health)"
    fi
else
    maybe "无法检查 HTTP 服务状态"
fi

# ── 8. 插件目录 ────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}[8/10] 插件${NC}"

PLUGIN_DIR="$PROJECT_ROOT/plugins"
if [ -d "$PLUGIN_DIR" ]; then
    PLUGIN_COUNT=$(find "$PLUGIN_DIR" -name "*.py" -not -name "__init__.py" 2>/dev/null | wc -l)
    if [ "$PLUGIN_COUNT" -gt 0 ]; then
        ok "发现 $PLUGIN_COUNT 个插件"
        find "$PLUGIN_DIR" -name "*.py" -not -name "__init__.py" -exec basename {} \; 2>/dev/null | while read -r p; do
            echo "    - $p"
        done
    else
        maybe "插件目录为空"
    fi
else
    maybe "插件目录不存在"
fi

# ── 9. 配置 ────────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}[9/10] 配置${NC}"

ENV_FILE="$PROJECT_ROOT/.env"
if [ -f "$ENV_FILE" ]; then
    ok ".env 文件存在"
    if grep -q "SECRET_KEY=" "$ENV_FILE" 2>/dev/null; then
        KEY_VAL=$(grep "SECRET_KEY=" "$ENV_FILE" | head -1 | cut -d= -f2)
        if [ -z "$KEY_VAL" ] || [ "$KEY_VAL" = "changeme" ] || [ "$KEY_VAL" = "your-secret-key" ]; then
            maybe "SECRET_KEY 使用默认值，生产环境请修改"
        else
            ok "SECRET_KEY 已配置"
        fi
    else
        maybe ".env 中未设置 SECRET_KEY"
    fi
else
    maybe ".env 文件不存在 (参考 .env.example 创建)"
fi

# ── 10. 磁盘空间 ──────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}[10/10] 磁盘空间${NC}"

if command -v df >/dev/null 2>&1; then
    FREE_PCT=$(df "$PROJECT_ROOT" 2>/dev/null | awk 'NR==2{print $5}' | tr -d '%')
    FREE_GB=$(df -h "$PROJECT_ROOT" 2>/dev/null | awk 'NR==2{print $4}')
    if [ -n "$FREE_PCT" ]; then
        USED_PCT="$FREE_PCT"
        AVAIL_PCT=$((100 - USED_PCT))
        if [ "$AVAIL_PCT" -gt 20 ]; then
            ok "磁盘空间充足 (${AVAIL_PCT}% 可用, ${FREE_GB} 剩余)"
        elif [ "$AVAIL_PCT" -gt 10 ]; then
            maybe "磁盘空间偏低 (${AVAIL_PCT}% 可用, ${FREE_GB} 剩余)"
        else
            no "磁盘空间严重不足 (${AVAIL_PCT}% 可用, ${FREE_GB} 剩余)"
        fi
    else
        maybe "无法检测磁盘空间"
    fi
else
    maybe "无法检测磁盘空间 (df 命令不可用)"
fi

# ── 汇总 ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}=== 诊断汇总 ===${NC}"
echo -e "  ${GREEN}通过: $pass${NC}  ${YELLOW}警告: $warn${NC}  ${RED}失败: $fail${NC}"
echo ""

if [ "$fail" -gt 0 ]; then
    echo -e "${RED}存在 $fail 个失败项，请根据上述提示修复后重试。${NC}"
    echo ""
    exit 1
elif [ "$warn" -gt 0 ]; then
    echo -e "${YELLOW}存在 $warn 个警告，建议检查但不影响基本功能。${NC}"
    echo ""
    exit 0
else
    echo -e "${GREEN}所有检查通过！智桥环境就绪。${NC}"
    echo ""
    exit 0
fi
