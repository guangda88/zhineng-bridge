/**
 * 动态导入模块
 */

// 动态导入工具模块
export async function importTools() {
  const { renderTools, selectTool, TOOLS } = await import('./tools.js');
  return { renderTools, selectTool, TOOLS };
}

// 动态导入会话模块
export async function importSessions() {
  const {
    renderSessions,
    newSession,
    refreshSessions,
    openSession,
    startSession,
    stopSession,
    deleteSession,
    renderSessionDetail,
    SESSIONS
  } = await import('./sessions.js');
  return {
    renderSessions,
    newSession,
    refreshSessions,
    openSession,
    startSession,
    stopSession,
    deleteSession,
    renderSessionDetail,
    SESSIONS
  };
}

// 动态导入设置模块
export async function importSettings() {
  const {
    SETTINGS,
    renderSettings,
    updateSetting,
    saveSettings,
    loadSettings,
    resetSettings,
    applyTheme
  } = await import('./settings.js');
  return {
    SETTINGS,
    renderSettings,
    updateSetting,
    saveSettings,
    loadSettings,
    resetSettings,
    applyTheme
  };
}

// 动态导入客户端模块
export async function importClient() {
  const {
    connectWebSocket,
    disconnectWebSocket,
    sendMessage,
    ws
  } = await import('./client.js');
  return {
    connectWebSocket,
    disconnectWebSocket,
    sendMessage,
    ws
  };
}
