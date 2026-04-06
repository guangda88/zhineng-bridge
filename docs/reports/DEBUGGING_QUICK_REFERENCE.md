# 代码问题诊断快速参考卡片

## 🚨 常见症状速查表

| 症状 | 可能原因 | 快速检查 | 立即行动 |
|------|----------|----------|----------|
| `undefined` | 作用域问题 | `console.log(typeof var)` | 检查变量声明位置 |
| `null` | 未初始化 | `console.log(var === null)` | 提供默认值 |
| `NaN` | 类型转换 | `console.log(isNaN(var))` | 使用 `parseInt()` 或 `Number()` |
| 对象方法不存在 | 类型错误 | `console.log(var.constructor.name)` | 检查数据类型 |
| 事件不触发 | 未绑定 | `getEventListeners(element)` | 检查事件监听器 |
| DOM 元素未找到 | 时序问题 | `console.log(document.querySelector)` | 等待 DOM 加载 |
| Promise pending | 未等待 | `console.log(obj instanceof Promise)` | 使用 `await` 或 `.then()` |

---

## 🔍 诊断命令速查

### JavaScript

```javascript
// 检查变量
console.log('变量:', variable);
console.log('类型:', typeof variable);
console.log('存在:', typeof variable !== 'undefined');

// 检查对象
console.log('属性:', Object.keys(obj));
console.log('原型:', obj.constructor.name);

// 检查数组
console.log('长度:', arr.length);
console.log('是数组:', Array.isArray(arr));

// 检查 DOM
console.log('元素:', document.getElementById('id'));
console.log('存在:', document.getElementById('id') !== null);

// 检查 Promise
console.log('是 Promise:', promise instanceof Promise);
console.log('状态:', promise._state);  // 部分库支持
```

### Python

```python
# 检查变量
print(f"变量: {variable}")
print(f"类型: {type(variable)}")
print(f"存在: {'variable' in locals()}")

# 检查对象
print(f"属性: {dir(obj)}")
print(f"方法: {vars(obj)}")

# 检查异常
try:
    operation()
except Exception as e:
    print(f"错误类型: {type(e).__name__}")
    print(f"错误信息: {str(e)}")
    import traceback
    traceback.print_exc()
```

---

## 🛠️ 修复模式速查

### 1. 作用域修复

```javascript
// ❌ 问题
const tools = [...];
function render() { tools.forEach(...); }  // 作用域外

// ✅ 修复 1: 挂载到 window
window.tools = [...];
function render() { window.tools.forEach(...); }

// ✅ 修复 2: ES6 模块
export const tools = [...];
import { tools } from './tools.js';
```

### 2. 异步修复

```javascript
// ❌ 问题
const data = fetchData();  // Promise
process(data);

// ✅ 修复 1: async/await
async function main() {
    const data = await fetchData();
    process(data);
}

// ✅ 修复 2: then
fetchData().then(data => {
    process(data);
});
```

### 3. DOM 时序修复

```javascript
// ❌ 问题
const el = document.getElementById('id');
el.addEventListener('click', handler);

// ✅ 修复 1: DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
    const el = document.getElementById('id');
    el.addEventListener('click', handler);
});

// ✅ 修复 2: 事件委托
document.addEventListener('click', (e) => {
    if (e.target.id === 'id') {
        handler(e);
    }
});

// ✅ 修复 3: 放在 body 底部
<script>
    // 此时 DOM 已加载
    const el = document.getElementById('id');
</script>
```

### 4. 类型修复

```javascript
// ❌ 问题
const num = "42";
if (num === 42) { }  // 永远 false

// ✅ 修复 1: 显式转换
const num = parseInt("42", 10);
if (num === 42) { }

// ✅ 修复 2: 宽松比较
const num = "42";
if (num == 42) { }

// ✅ 修复 3: Number 类型
const num = Number("42");
if (num === 42) { }
```

---

## 🎯 5分钟诊断流程

```
1. 添加日志 (30秒)
   console.log('关键变量:', variable);
   console.log('类型:', typeof variable);

2. 检查浏览器控制台 (30秒)
   - 是否有错误？
   - 错误发生在哪一行？
   - 调用栈是什么？

3. 验证假设 (1分钟)
   - 变量是否正确赋值？
   - 函数是否被调用？
   - 异步是否完成？

4. 简化代码 (2分钟)
   - 创建最小可重现示例
   - 移除不相关的代码
   - 逐步添加功能

5. 查阅文档 (1分钟)
   - API 文档
   - 类似问题
   - 已知 issues
```

---

## 🚀 调试工具快捷键

### Chrome DevTools

| 功能 | 快捷键 | 说明 |
|------|---------|------|
| 打开 DevTools | F12 / Ctrl+Shift+I | 打开开发者工具 |
| 控制台 | Ctrl+` | 切换控制台 |
| 元素检查 | Ctrl+Shift+C | 选择元素 |
| 暂停脚本 | F8 | 暂停执行 |
| 单步执行 | F10 | 单步跳过 |
| 进入函数 | F11 | 单步进入 |
| 跳出函数 | Shift+F11 | 单步跳出 |
| 断点 | Ctrl+B | 在当前行设置断点 |

### VS Code

| 功能 | 快捷键 | 说明 |
|------|---------|------|
| 调试 | F5 | 开始调试 |
| 暂停 | Shift+F9 | 切换断点 |
| 单步跳过 | F10 | 单步跳过 |
| 单步进入 | F11 | 单步进入 |
| 单步跳出 | Shift+F11 | 单步跳出 |
| 控制台 | Ctrl+` | 打开集成终端 |

---

## 📊 问题分类决策树

```
问题发生？
│
├─ 运行时错误（红色错误）
│  │
│  ├─ ReferenceError: variable is not defined
│  │  └─> 变量未声明或作用域错误
│  │     → 检查变量声明位置
│  │     → 使用 window 或 export/import
│  │
│  ├─ TypeError: Cannot read property 'x' of undefined
│  │  └─> 对象为 null/undefined
│  │     → 添加空值检查
│  │     → 提供默认值
│  │
│  └─ TypeError: ... is not a function
│     └─> 类型错误
│        → 检查实际类型
│        → 验证函数存在
│
├─ 逻辑错误（无错误，但结果错误）
│  │
│  ├─ 变量值不符合预期
│  │  └─> 添加日志追踪
│  │     → 检查赋值时机
│  │     → 验证计算逻辑
│  │
│  └─ 异步操作未完成
│     └─> 检查 Promise 状态
│        → 添加 await 或 then
│        → 使用 Promise.all
│
└─ 无任何输出（静默失败）
   │
   ├─ 代码未执行
   │  └─> 检查函数调用
   │     → 验证条件判断
   │     → 添加日志确认执行
   │
   └─ 错误被吞掉
      → 检查 try/catch
      → 添加错误日志
      → 使用 console.error
```

---

## 🔧 常用代码片段

### 防御性编程

```javascript
// 安全访问对象属性
const value = object?.nested?.property ?? defaultValue;

// 安全调用方法
const result = object?.method?.() ?? defaultValue;

// 安全数组访问
const item = array?.[index] ?? defaultValue;
```

### 日志包装器

```javascript
const log = {
    data: (label, data) => console.log(`📊 ${label}:`, data),
    error: (label, error) => console.error(`❌ ${label}:`, error),
    warn: (label, warning) => console.warn(`⚠️  ${label}:`, warning),
    debug: (label, ...args) => console.log(`🔍 ${label}:`, ...args),
    group: (label) => console.group(`📁 ${label}`),
    groupEnd: () => console.groupEnd(),
    time: (label) => console.time(`⏱️  ${label}`),
    timeEnd: (label) => console.timeEnd(`⏱️  ${label}`)
};

// 使用
log.group('处理流程');
log.data('输入数据', data);
log.time('处理时间');
const result = process(data);
log.timeEnd('处理时间');
log.data('输出结果', result);
log.groupEnd();
```

### 错误边界（React）

```javascript
class ErrorBoundary extends React.Component {
    state = { hasError: false, error: null };

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        console.error('错误捕获:', error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return <ErrorFallback error={this.state.error} />;
        }
        return this.props.children;
    }
}
```

---

## 📞 获取帮助

### 提问模板

```
问题描述：
[简短描述问题]

预期行为：
[期望的结果]

实际行为：
[实际发生的情况]

重现步骤：
1. [步骤 1]
2. [步骤 2]
3. [步骤 3]

代码片段：
```javascript
// 最小可重现代码
```

错误信息：
[控制台/终端错误]

环境信息：
- 浏览器/Node 版本:
- 操作系统:
- 相关库版本:

已尝试：
1. [尝试 1]
2. [尝试 2]
```

---

**更新时间**: 2026-03-27
**版本**: 1.0
**相关文档**: SOLVING_CODE_ISSUES_GUIDE.md
