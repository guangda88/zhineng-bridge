/**
 * 智桥 - Web Worker
 */

self.addEventListener('message', (event) => {
    const { type, data } = event.data;
    
    console.log('📨 Worker 收到消息:', type);
    
    switch (type) {
        case 'optimize':
            optimizeData(data);
            break;
        case 'compute':
            computeData(data);
            break;
        default:
            console.warn('⚠️  未知消息类型:', type);
    }
});

function optimizeData(data) {
    // 优化数据
    const optimized = JSON.parse(JSON.stringify(data));
    
    // 发送优化后的数据
    self.postMessage({
        type: 'optimized',
        data: optimized
    });
}

function computeData(data) {
    // 计算数据
    const result = {
        count: Object.keys(data).length,
        size: JSON.stringify(data).length
    };
    
    // 发送计算结果
    self.postMessage({
        type: 'computed',
        data: result
    });
}
