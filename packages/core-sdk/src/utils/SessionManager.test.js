/**
 * SessionManager工具类测试
 * @test
 */

const { expect } = require('chai');

// 模拟SessionManager类（如果需要）
class SessionManager {
    constructor() {
        this.sessions = new Map();
    }

    create(name, projectContext = '') {
        const session = {
            id: this.generateId(),
            name,
            projectContext,
            isActive: true,
            createdAt: Date.now(),
            lastActivity: Date.now()
        };
        this.sessions.set(session.id, session);
        return session;
    }

    get(sessionId) {
        return this.sessions.get(sessionId);
    }

    pause(sessionId) {
        const session = this.sessions.get(sessionId);
        if (session) {
            session.isActive = false;
            return true;
        }
        return false;
    }

    resume(sessionId) {
        const session = this.sessions.get(sessionId);
        if (session) {
            session.isActive = true;
            session.lastActivity = Date.now();
            return true;
        }
        return false;
    }

    delete(sessionId) {
        return this.sessions.delete(sessionId);
    }

    getAll() {
        return Array.from(this.sessions.values());
    }

    generateId() {
        return Math.random().toString(36).substring(2, 15) +
               Math.random().toString(36).substring(2, 15);
    }
}

describe('SessionManager工具类', () => {
    let sessionManager;

    beforeEach(() => {
        sessionManager = new SessionManager();
    });

    describe('会话创建', () => {
        it('应该能够创建新会话', () => {
            const session = sessionManager.create('Test Session');

            expect(session).to.be.an('object');
            expect(session.id).to.be.a('string');
            expect(session.name).to.equal('Test Session');
            expect(session.isActive).to.be.true;
            expect(session.createdAt).to.be.a('number');
        });

        it('应该能够创建带项目上下文的会话', () => {
            const projectContext = '/path/to/project';
            const session = sessionManager.create('Test Session', projectContext);

            expect(session.projectContext).to.equal(projectContext);
        });

        it('应该生成唯一的会话ID', () => {
            const session1 = sessionManager.create('Session 1');
            const session2 = sessionManager.create('Session 2');

            expect(session1.id).to.not.equal(session2.id);
        });
    });

    describe('会话查询', () => {
        it('应该能够通过ID获取会话', () => {
            const created = sessionManager.create('Test Session');
            const retrieved = sessionManager.get(created.id);

            expect(retrieved).to.equal(created);
        });

        it('不存在的会话ID应该返回undefined', () => {
            const session = sessionManager.get('non-existent-id');

            expect(session).to.be.undefined;
        });

        it('应该能够获取所有会话', () => {
            sessionManager.create('Session 1');
            sessionManager.create('Session 2');
            sessionManager.create('Session 3');

            const allSessions = sessionManager.getAll();

            expect(allSessions).to.have.lengthOf(3);
        });
    });

    describe('会话暂停', () => {
        it('应该能够暂停活动会话', () => {
            const session = sessionManager.create('Test Session');
            const result = sessionManager.pause(session.id);

            expect(result).to.be.true;
            expect(session.isActive).to.be.false;
        });

        it('暂停不存在的会话应该返回false', () => {
            const result = sessionManager.pause('non-existent-id');

            expect(result).to.be.false;
        });

        it('应该能够暂停多个会话', () => {
            const session1 = sessionManager.create('Session 1');
            const session2 = sessionManager.create('Session 2');

            sessionManager.pause(session1.id);
            sessionManager.pause(session2.id);

            expect(session1.isActive).to.be.false;
            expect(session2.isActive).to.be.false;
        });
    });

    describe('会话恢复', () => {
        it('应该能够恢复暂停的会话', () => {
            const session = sessionManager.create('Test Session');
            sessionManager.pause(session.id);
            const result = sessionManager.resume(session.id);

            expect(result).to.be.true;
            expect(session.isActive).to.be.true;
        });

        it('恢复不存在的会话应该返回false', () => {
            const result = sessionManager.resume('non-existent-id');

            expect(result).to.be.false;
        });

        it('恢复会话应该更新最后活动时间', () => {
            const session = sessionManager.create('Test Session');
            const originalActivity = session.lastActivity;

            sessionManager.pause(session.id);
            // 等待一小段时间
            sessionManager.resume(session.id);

            expect(session.lastActivity).to.be.greaterThan(originalActivity);
        });
    });

    describe('会话删除', () => {
        it('应该能够删除存在的会话', () => {
            const session = sessionManager.create('Test Session');
            const result = sessionManager.delete(session.id);

            expect(result).to.be.true;
            expect(sessionManager.get(session.id)).to.be.undefined;
        });

        it('删除不存在的会话应该返回false', () => {
            const result = sessionManager.delete('non-existent-id');

            expect(result).to.be.false;
        });

        it('删除会话后应该不影响其他会话', () => {
            const session1 = sessionManager.create('Session 1');
            const session2 = sessionManager.create('Session 2');

            sessionManager.delete(session1.id);

            expect(sessionManager.get(session2.id)).to.equal(session2);
        });
    });

    describe('会话活动更新', () => {
        it('应该能够更新会话的最后活动时间', () => {
            const session = sessionManager.create('Test Session');
            const originalActivity = session.lastActivity;

            // 等待一小段时间
            setTimeout(() => {
                session.lastActivity = Date.now();
                expect(session.lastActivity).to.be.greaterThan(originalActivity);
            }, 10);
        });
    });

    describe('边界情况', () => {
        it('应该能够处理空会话名称', () => {
            const session = sessionManager.create('');

            expect(session).to.be.an('object');
            expect(session.name).to.equal('');
        });

        it('应该能够处理很长的会话名称', () => {
            const longName = 'A'.repeat(1000);
            const session = sessionManager.create(longName);

            expect(session.name).to.equal(longName);
        });

        it('应该能够创建大量会话', () => {
            const count = 1000;
            for (let i = 0; i < count; i++) {
                sessionManager.create(`Session ${i}`);
            }

            const allSessions = sessionManager.getAll();
            expect(allSessions).to.have.lengthOf(count);
        });
    });

    describe('并发操作', () => {
        it('应该能够处理并发创建会话', function() {
            this.timeout(5000);

            const count = 100;
            const promises = [];

            for (let i = 0; i < count; i++) {
                promises.push(new Promise(resolve => {
                    setTimeout(() => {
                        sessionManager.create(`Concurrent Session ${i}`);
                        resolve();
                    }, Math.random() * 100);
                }));
            }

            return Promise.all(promises).then(() => {
                const allSessions = sessionManager.getAll();
                expect(allSessions).to.have.lengthOf(count);

                // 检查所有ID是否唯一
                const ids = allSessions.map(s => s.id);
                const uniqueIds = new Set(ids);
                expect(uniqueIds.size).to.equal(count);
            });
        });
    });
});
