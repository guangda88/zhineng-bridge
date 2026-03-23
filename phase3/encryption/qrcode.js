/**
 * 智桥 - QR 码模块
 * 使用 QRCode.js 库生成 QR 码
 */

class QRCodeManager {
    constructor(encryptionManager) {
        this.encryptionManager = encryptionManager;
        this.qrCode = null;
        this.initialized = false;
    }

    /**
     * 初始化 QR 码管理器
     */
    async init() {
        if (this.initialized) {
            console.warn('⚠️  QR 码管理器已初始化');
            return;
        }

        console.log('📱 初始化 QR 码管理器');

        // 加载 QRCode.js 库
        await this.loadQRCodeLibrary();
        
        this.initialized = true;
        console.log('✅ QR 码管理器已初始化');
    }

    /**
     * 加载 QRCode.js 库
     */
    async loadQRCodeLibrary() {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/qrcode@1.5.1/build/qrcode.min.js';
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    /**
     * 生成密钥交换 QR 码
     */
    async generateKeyExchangeQRCode() {
        try {
            // 导出公钥
            const publicKey = await this.encryptionManager.exportPublicKey();
            
            // 生成 QR 码数据
            const qrData = {
                type: 'key_exchange',
                publicKey: publicKey,
                timestamp: new Date().toISOString(),
                deviceId: this.generateDeviceId()
            };

            // 转换为 JSON 字符串
            const qrString = JSON.stringify(qrData);

            // 生成 QR 码
            const qrContainer = document.createElement('div');
            qrContainer.className = 'qr-code-container';
            await QRCode.toCanvas(qrString, { width: 256 }, (error, canvas) => {
                if (error) {
                    console.error('❌ 生成 QR 码失败:', error);
                    throw error;
                }
                qrContainer.appendChild(canvas);
            });

            console.log('✅ 密钥交换 QR 码已生成');
            return qrContainer;
        } catch (error) {
            console.error('❌ 生成密钥交换 QR 码失败:', error);
            throw error;
        }
    }

    /**
     * 扫描 QR 码
     */
    async scanQRCode(qrString) {
        try {
            // 解析 QR 码数据
            const qrData = JSON.parse(qrString);
            
            // 验证 QR 码类型
            if (qrData.type !== 'key_exchange') {
                throw new Error('无效的 QR 码类型');
            }

            // 导入公钥
            const publicKey = await this.encryptionManager.importPublicKey(qrData.publicKey);

            // 生成会话密钥
            const { sessionKey, sessionKeyId } = await this.encryptionManager.generateSessionKey();

            // 导出会话密钥（使用对方的公钥加密）
            const sessionKeyData = await window.crypto.subtle.exportKey(
                "raw",
                sessionKey
            );
            const encryptedSessionKey = await this.encryptionManager.encryptMessage(
                this.arrayBufferToBase64(sessionKeyData),
                publicKey
            );

            console.log('✅ QR 码已扫描，会话密钥已建立');
            return {
                sessionKeyId,
                encryptedSessionKey,
                timestamp: qrData.timestamp,
                deviceId: qrData.deviceId
            };
        } catch (error) {
            console.error('❌ 扫描 QR 码失败:', error);
            throw error;
        }
    }

    /**
     * ArrayBuffer 转 Base64
     */
    arrayBufferToBase64(buffer) {
        const bytes = new Uint8Array(buffer);
        let binary = '';
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return window.btoa(binary);
    }

    /**
     * 生成设备 ID
     */
    generateDeviceId() {
        let deviceId = localStorage.getItem('zhineng-bridge-device-id');
        if (!deviceId) {
            deviceId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                const r = Math.random() * 16 | 0;
                const v = c == 'x' ? r : (r & 0x3 | 0x8);
                return v.toString(16);
            });
            localStorage.setItem('zhineng-bridge-device-id', deviceId);
        }
        return deviceId;
    }
}

// 导出 QR 码管理器
window.QRCodeManager = QRCodeManager;
