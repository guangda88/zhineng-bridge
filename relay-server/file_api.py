#!/usr/bin/env python3
"""
文件 API 模块

提供安全的文件读取、搜索、统计和列表功能
"""

import mimetypes
import os
import re
from pathlib import Path

from aiohttp import web
from logger import get_logger


class FileAPI:
    """文件 API 处理类"""

    # 安全配置
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {
        ".txt",
        ".md",
        ".py",
        ".js",
        ".ts",
        ".html",
        ".css",
        ".json",
        ".yaml",
        ".yml",
        ".xml",
        ".ini",
        ".cfg",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".java",
        ".go",
        ".rs",
        ".sh",
        ".bash",
        ".zsh",
        ".fish",
        ".log",
        ".csv",
    }

    # 禁止访问的目录（安全黑名单）
    BLACKLIST_DIRS = {"/etc", "/sys", "/proc", "/dev", "/root", "~/.ssh", "~/.gnupg", "~/.config"}

    # 默认允许访问的目录（相对于项目根目录）
    DEFAULT_ALLOWED_DIRS = [
        "/home/ai/zhineng-bridge",
        "/home/ai/zhineng-bridge/web",
        "/home/ai/zhineng-bridge/relay-server",
        "/home/ai/zhineng-bridge/phase1",
        "/home/ai/zhineng-bridge/docs",
    ]

    def __init__(self, base_dir: str = None):
        """
        初始化文件 API

        Args:
            base_dir: 基础目录（默认使用项目根目录）
        """
        self.logger = get_logger(__name__)
        self.base_dir = base_dir or "/home/ai/zhineng-bridge"
        self.allowed_dirs = self.DEFAULT_ALLOWED_DIRS.copy()
        self.cache = {}  # 简单的内存缓存

    def _validate_path(self, file_path: str) -> Path:
        """
        验证文件路径安全性

        Args:
            file_path: 文件路径

        Returns:
            验证后的绝对路径

        Raises:
            ValueError: 路径不安全或无效
        """
        # 转换为绝对路径
        if not os.path.isabs(file_path):
            # 相对路径，相对于基础目录
            abs_path = Path(self.base_dir) / file_path
        else:
            abs_path = Path(file_path)

        # 转换为绝对路径（解析 .. 和符号链接）
        abs_path = abs_path.resolve()

        # 检查路径遍历攻击（防止访问上级目录）
        if ".." in str(abs_path.parts):
            raise ValueError("Path traversal attack detected")

        # 检查是否在黑名单目录中
        path_str = str(abs_path)
        for blacklist_dir in self.BLACKLIST_DIRS:
            if path_str.startswith(blacklist_dir):
                raise ValueError(f"Access to blacklisted directory: {blacklist_dir}")

        # 检查是否在允许的目录中
        is_allowed = False
        for allowed_dir in self.allowed_dirs:
            if path_str.startswith(allowed_dir):
                is_allowed = True
                break

        if not is_allowed:
            raise ValueError("Access denied: path not in allowed directories")

        # 检查文件扩展名
        if abs_path.is_file():
            ext = abs_path.suffix.lower()
            if ext and ext not in self.ALLOWED_EXTENSIONS:
                raise ValueError(f"File extension not allowed: {ext}")

        return abs_path

    def _check_file_permissions(self, file_path: Path) -> None:
        """
        检查文件权限

        Args:
            file_path: 文件路径

        Raises:
            PermissionError: 权限不足
        """
        # 检查读取权限
        if not os.access(file_path, os.R_OK):
            raise PermissionError(f"Read permission denied: {file_path}")

        # 检查文件大小
        try:
            file_size = file_path.stat().st_size
            if file_size > self.MAX_FILE_SIZE:
                raise ValueError(f"File too large: {file_size} bytes (max: {self.MAX_FILE_SIZE})")
        except OSError as e:
            raise PermissionError(f"Cannot access file: {e}")

    async def read_file(self, request: web.Request) -> web.Response:
        """
        读取文件内容

        GET /api/files/read?path=/path/to/file.txt

        Args:
            request: HTTP 请求

        Returns:
            JSON 响应包含文件内容
        """
        try:
            file_path = request.query.get("path")

            if not file_path:
                return web.json_response(
                    {"type": "error", "message": "Missing 'path' parameter", "code": 400},
                    status=400,
                )

            # 验证路径安全性
            validated_path = self._validate_path(file_path)

            # 检查是否为文件
            if not validated_path.is_file():
                return web.json_response(
                    {"type": "error", "message": f"Not a file: {file_path}", "code": 404},
                    status=404,
                )

            # 检查文件权限
            self._check_file_permissions(validated_path)

            # 检查缓存
            cache_key = str(validated_path)
            if cache_key in self.cache:
                mtime = validated_path.stat().st_mtime
                cached = self.cache[cache_key]
                if cached["mtime"] == mtime:
                    self.logger.debug("File cache hit", path=file_path)
                    return web.json_response(cached["data"])

            # 读取文件内容
            try:
                with open(validated_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            except UnicodeDecodeError:
                # 如果是二进制文件，返回错误
                return web.json_response(
                    {"type": "error", "message": "Cannot read binary file", "code": 400}, status=400
                )

            # 获取文件元数据
            stat = validated_path.stat()
            mime_type, _ = mimetypes.guess_type(str(validated_path))

            # 构建响应数据
            data = {
                "type": "file_content",
                "path": str(validated_path),
                "content": content,
                "metadata": {
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "mime_type": mime_type or "text/plain",
                    "extension": validated_path.suffix,
                },
            }

            # 缓存结果
            self.cache[cache_key] = {"mtime": stat.st_mtime, "data": data}

            self.logger.info("File read successfully", path=file_path, size=stat.st_size)

            return web.json_response(data)

        except ValueError as e:
            self.logger.warning("Path validation failed", path=file_path, error=str(e))
            return web.json_response({"type": "error", "message": str(e), "code": 400}, status=400)
        except PermissionError as e:
            self.logger.warning("Permission denied", path=file_path, error=str(e))
            return web.json_response({"type": "error", "message": str(e), "code": 403}, status=403)
        except Exception as e:
            self.logger.error("File read failed", path=file_path, error=str(e), exc_info=True)
            return web.json_response(
                {"type": "error", "message": f"Failed to read file: {str(e)}", "code": 500},
                status=500,
            )

    async def search_files(self, request: web.Request) -> web.Response:
        """
        搜索文件

        GET /api/files/search?query=search_term&path=/path/to/search&limit=100&offset=0

        Args:
            request: HTTP 请求

        Returns:
            JSON 响应包含匹配的文件列表
        """
        try:
            query = request.query.get("query", "").strip()
            search_path = request.query.get("path", self.base_dir)
            limit = int(request.query.get("limit", 50))
            offset = int(request.query.get("offset", 0))

            if not query:
                return web.json_response(
                    {"type": "error", "message": "Missing 'query' parameter", "code": 400},
                    status=400,
                )

            # 验证搜索路径
            validated_path = self._validate_path(search_path)

            if not validated_path.exists():
                return web.json_response(
                    {
                        "type": "error",
                        "message": f"Search path does not exist: {search_path}",
                        "code": 404,
                    },
                    status=404,
                )

            # 搜索文件
            results = []
            count = 0

            # 使用模糊搜索
            query_pattern = re.compile(re.escape(query), re.IGNORECASE)

            for file_path in validated_path.rglob("*"):
                if file_path.is_file():
                    # 检查文件名匹配
                    if query_pattern.search(file_path.name):
                        if count >= offset and len(results) < limit:
                            try:
                                stat = file_path.stat()
                                results.append(
                                    {
                                        "path": str(file_path),
                                        "name": file_path.name,
                                        "size": stat.st_size,
                                        "modified": stat.st_mtime,
                                        "extension": file_path.suffix,
                                    }
                                )
                            except OSError:
                                pass
                        count += 1

            self.logger.info(
                "File search completed",
                query=query,
                path=search_path,
                matches=len(results),
                total=count,
            )

            return web.json_response(
                {
                    "type": "search_results",
                    "query": query,
                    "path": search_path,
                    "results": results,
                    "count": len(results),
                    "total": count,
                    "limit": limit,
                    "offset": offset,
                }
            )

        except ValueError as e:
            self.logger.warning("Search validation failed", error=str(e))
            return web.json_response({"type": "error", "message": str(e), "code": 400}, status=400)
        except Exception as e:
            self.logger.error("File search failed", error=str(e), exc_info=True)
            return web.json_response(
                {"type": "error", "message": f"Failed to search files: {str(e)}", "code": 500},
                status=500,
            )

    async def get_file_stats(self, request: web.Request) -> web.Response:
        """
        获取文件统计信息

        GET /api/files/stats?path=/path/to/file

        Args:
            request: HTTP 请求

        Returns:
            JSON 响应包含文件元数据
        """
        try:
            file_path = request.query.get("path")

            if not file_path:
                return web.json_response(
                    {"type": "error", "message": "Missing 'path' parameter", "code": 400},
                    status=400,
                )

            # 验证路径
            validated_path = self._validate_path(file_path)

            if not validated_path.exists():
                return web.json_response(
                    {"type": "error", "message": f"File not found: {file_path}", "code": 404},
                    status=404,
                )

            # 获取文件统计信息
            stat = validated_path.stat()
            mime_type, _ = mimetypes.guess_type(str(validated_path))

            data = {
                "type": "file_stats",
                "path": str(validated_path),
                "name": validated_path.name,
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "created": stat.st_ctime,
                "is_file": validated_path.is_file(),
                "is_dir": validated_path.is_dir(),
                "extension": validated_path.suffix,
                "mime_type": mime_type
                or ("inode/directory" if validated_path.is_dir() else "application/octet-stream"),
            }

            # 如果是目录，添加文件计数
            if validated_path.is_dir():
                file_count = 0
                dir_count = 0
                for _ in validated_path.iterdir():
                    if _.is_file():
                        file_count += 1
                    elif _.is_dir():
                        dir_count += 1
                data["directory"] = {"file_count": file_count, "dir_count": dir_count}

            self.logger.info("File stats retrieved", path=file_path)

            return web.json_response(data)

        except ValueError as e:
            self.logger.warning("Stats validation failed", error=str(e))
            return web.json_response({"type": "error", "message": str(e), "code": 400}, status=400)
        except Exception as e:
            self.logger.error("Get file stats failed", error=str(e), exc_info=True)
            return web.json_response(
                {"type": "error", "message": f"Failed to get file stats: {str(e)}", "code": 500},
                status=500,
            )

    async def list_files(self, request: web.Request) -> web.Response:
        """
        列出目录中的文件

        GET /api/files/list?path=/path/to/dir&recursive=false&limit=100&offset=0

        Args:
            request: HTTP 请求

        Returns:
            JSON 响应包含文件列表
        """
        try:
            dir_path = request.query.get("path", self.base_dir)
            recursive = request.query.get("recursive", "false").lower() == "true"
            limit = int(request.query.get("limit", 100))
            offset = int(request.query.get("offset", 0))

            # 验证路径
            validated_path = self._validate_path(dir_path)

            if not validated_path.exists():
                return web.json_response(
                    {"type": "error", "message": f"Directory not found: {dir_path}", "code": 404},
                    status=404,
                )

            if not validated_path.is_dir():
                return web.json_response(
                    {"type": "error", "message": f"Not a directory: {dir_path}", "code": 400},
                    status=400,
                )

            # 列出文件
            files = []
            count = 0

            if recursive:
                # 递归列出所有文件
                for file_path in validated_path.rglob("*"):
                    if count >= offset and len(files) < limit:
                        try:
                            stat = file_path.stat()
                            files.append(
                                {
                                    "path": str(file_path.relative_to(validated_path)),
                                    "name": file_path.name,
                                    "size": stat.st_size,
                                    "modified": stat.st_mtime,
                                    "is_file": file_path.is_file(),
                                    "is_dir": file_path.is_dir(),
                                    "extension": file_path.suffix,
                                }
                            )
                        except OSError:
                            pass
                    count += 1
            else:
                # 只列出直接子项
                for item in validated_path.iterdir():
                    if count >= offset and len(files) < limit:
                        try:
                            stat = item.stat()
                            files.append(
                                {
                                    "path": str(item.relative_to(validated_path)),
                                    "name": item.name,
                                    "size": stat.st_size,
                                    "modified": stat.st_mtime,
                                    "is_file": item.is_file(),
                                    "is_dir": item.is_dir(),
                                    "extension": item.suffix,
                                }
                            )
                        except OSError:
                            pass
                    count += 1

            # 按类型和名称排序
            files.sort(key=lambda x: (not x["is_dir"], x["name"]))

            self.logger.info(
                "File list retrieved",
                path=dir_path,
                count=len(files),
                total=count,
                recursive=recursive,
            )

            return web.json_response(
                {
                    "type": "file_list",
                    "path": dir_path,
                    "recursive": recursive,
                    "files": files,
                    "count": len(files),
                    "total": count,
                    "limit": limit,
                    "offset": offset,
                }
            )

        except ValueError as e:
            self.logger.warning("List validation failed", error=str(e))
            return web.json_response({"type": "error", "message": str(e), "code": 400}, status=400)
        except Exception as e:
            self.logger.error("List files failed", error=str(e), exc_info=True)
            return web.json_response(
                {"type": "error", "message": f"Failed to list files: {str(e)}", "code": 500},
                status=500,
            )


# ============================================================================
# 辅助函数
# ============================================================================


def setup_file_routes(app: web.Application, file_api: FileAPI):
    """
    设置文件 API 路由

    Args:
        app: aiohttp 应用
        file_api: FileAPI 实例
    """
    # 文件读取
    app.router.add_get("/api/files/read", file_api.read_file)

    # 文件搜索
    app.router.add_get("/api/files/search", file_api.search_files)

    # 文件统计
    app.router.add_get("/api/files/stats", file_api.get_file_stats)

    # 文件列表
    app.router.add_get("/api/files/list", file_api.list_files)


__all__ = ["FileAPI", "setup_file_routes"]
