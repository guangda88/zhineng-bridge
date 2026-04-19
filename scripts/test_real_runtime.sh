#!/bin/bash
# 智桥实际运行测试脚本

echo "=========================================="
echo "🚀 智桥实际运行测试"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 第一步：检查依赖
echo -e "${BLUE}第一步：检查依赖${NC}"
echo "----------------------------------------"

command -v python3 >/dev/null 2>&1 || { echo -e "${RED}❌ python3 未安装${NC}"; exit 1; }
command -v crush >/dev/null 2>&1 || { echo -e "${YELLOW}⚠️  crush 未找到，测试将跳过Crush工具${NC}"; }

echo -e "${GREEN}✅ 依赖检查通过${NC}"
echo ""

# 第二步：启动中继服务器
echo -e "${BLUE}第二步：启动中继服务器${NC}"
echo "----------------------------------------"

# 检查8766端口是否被占用
if lsof -i :8766 >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  端口8766已被占用，停止现有服务${NC}"
    pkill -f "relay-server/server.py" 2>/dev/null || true
    sleep 2
fi

cd /home/ai/zhineng-bridge/relay-server
python3 start_server.py > /tmp/relay_server.log 2>&1 &
RELAY_PID=$!
echo "中继服务器启动中... PID: $RELAY_PID"

# 等待服务器启动
sleep 3

if ps -p $RELAY_PID > /dev/null; then
    echo -e "${GREEN}✅ 中继服务器已启动${NC}"
else
    echo -e "${RED}❌ 中继服务器启动失败${NC}"
    cat /tmp/relay_server.log
    exit 1
fi
echo ""

# 第三步：启动会话管理器
echo -e "${BLUE}第三步：启动会话管理器${NC}"
echo "----------------------------------------"

cd /home/ai/zhineng-bridge/phase1/session_manager
python3 start_manager.py > /tmp/session_manager.log 2>&1 &
MANAGER_PID=$!
echo "会话管理器启动中... PID: $MANAGER_PID"

sleep 2

if ps -p $MANAGER_PID > /dev/null; then
    echo -e "${GREEN}✅ 会话管理器已启动${NC}"
else
    echo -e "${YELLOW}⚠️  会话管理器启动（非必需，继续测试）${NC}"
    MANAGER_PID=""
fi
echo ""

# 第四步：运行测试脚本
echo -e "${BLUE}第四步：运行AI互联测试${NC}"
echo "----------------------------------------"

cd /home/ai/zhineng-bridge
python3 scripts/test_ai_communication.py
echo ""

# 第五步：清理
echo -e "${BLUE}第五步：清理进程${NC}"
echo "----------------------------------------"

if [ ! -z "$RELAY_PID" ] && ps -p $RELAY_PID > /dev/null; then
    echo "停止中继服务器 (PID: $RELAY_PID)..."
    kill $RELAY_PID 2>/dev/null
fi

if [ ! -z "$MANAGER_PID" ] && ps -p $MANAGER_PID > /dev/null; then
    echo "停止会话管理器 (PID: $MANAGER_PID)..."
    kill $MANAGER_PID 2>/dev/null
fi

echo -e "${GREEN}✅ 清理完成${NC}"
echo ""

echo "=========================================="
echo -e "${GREEN}🎉 测试完成！${NC}"
echo "=========================================="
echo ""
echo "日志文件："
echo "  - 中继服务器: /tmp/relay_server.log"
echo "  - 会话管理器: /tmp/session_manager.log"
echo ""
