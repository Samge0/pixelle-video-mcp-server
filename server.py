"""
视频生成 MCP 服务器
使用 FastMCP 将视频生成功能包装为 MCP 服务
"""
import logging
import os
from pathlib import Path
from typing import Dict
from fastmcp import FastMCP
from generate_video import generate_video

# 配置日志 - 使用进程 ID 区分不同客户端实例
log_dir = Path(__file__).parent / ".logs"
log_dir.mkdir(exist_ok=True)
# 使用进程 ID 作为日志文件名，避免多客户端冲突
pid = os.getpid()
log_file = log_dir / f"video_server_{pid}.log"

# 创建独立的 logger
logger = logging.getLogger("pixelle_video_server")
logger.setLevel(logging.INFO)

# 清除可能存在的 handlers
logger.handlers.clear()

# 创建文件 handler
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# 只添加文件 handler，不添加 StreamHandler（避免干扰 MCP stdio 通信）
logger.addHandler(file_handler)

# 防止日志传播到父 logger
logger.propagate = False

mcp = FastMCP("Pixelle Video Server")


@mcp.tool
async def generate_video_tool(
    text: str,
    slider_value: int = 5,
    tts_volume: float = 1.0,
    url: str = "http://localhost:58501/",
    headless: bool = False,
    timeout: int = 1200
) -> Dict[str, object]:
    """
    自动生成视频

    使用 Playwright 自动化操作 Streamlit 应用生成视频。

    Args:
        text: 要输入的文本内容
        slider_value: 分镜滑块值 (5-30)，默认 5
        tts_volume: TTS音量值 (0.1-5.0)，默认 1.0
        url: Streamlit 应用 URL，默认 http://localhost:58501/
        headless: 是否使用无头模式运行浏览器，默认 False
        timeout: 等待视频生成的超时时间（秒），默认 1200 (20分钟)

    Returns:
        包含状态和文件信息的字典：
        {
            "status": "success",
            "count": 2,
            "files": [
                {"path": "/path/to/video.mp4", "name": "video.mp4", "size": 1048576, "mimeType": "video/mp4"},
                ...
            ]
        }

    Raises:
        ValueError: 如果 TTS 音量值不在 0.1-5.0 范围内
    """
    # 验证参数
    if not 5 <= slider_value <= 30:
        raise ValueError("分镜滑块值必须在 5-30 之间")

    if not 0.1 <= tts_volume <= 5.0:
        raise ValueError("TTS音量值必须在 0.1-5.0 之间")

    # 记录调用信息
    logger.info(f"开始生成视频 - 文本: {text[:50]}{'...' if len(text) > 50 else ''}, 分镜: {slider_value}, 音量: {tts_volume}")

    # 调用生成视频函数
    downloaded_files = await generate_video(
        text=text,
        slider_value=slider_value,
        tts_volume=tts_volume,
        url=url,
        headless=headless,
        timeout=timeout
    )

    # 记录结果
    if downloaded_files:
        logger.info(f"视频生成成功，共 {len(downloaded_files)} 个文件")
        for f in downloaded_files:
            logger.info(f"  - {f}")

        return {
            "status": "success",
            "count": len(downloaded_files),
            "files": [
                {
                    "path": str(f),
                    "name": f.name,
                    "size": f.stat().st_size,
                    "mimeType": "video/mp4"
                }
                for f in downloaded_files
            ]
        }
    else:
        logger.warning("视频生成失败，未返回文件")
        return {
            "status": "failed",
            "count": 0,
            "files": []
        }


@mcp.resource("video://{filename}")
def get_video_file(filename: str) -> bytes:
    """
    通过 MCP Resource 协议获取视频文件内容

    Args:
        filename: 视频文件名（不含路径）

    Returns:
        视频文件的二进制内容
    """
    cache_dir = Path(__file__).parent / ".cache" / "videos"
    video_path = cache_dir / filename

    if not video_path.exists():
        raise FileNotFoundError(f"视频文件不存在: {filename}")

    return video_path.read_bytes()


@mcp.resource("cache://videos")
def list_cached_videos() -> str:
    """
    获取缓存目录中的所有视频文件列表

    Returns:
        缓存视频文件的列表信息
    """
    cache_dir = Path(__file__).parent / ".cache" / "videos"

    if not cache_dir.exists():
        return "缓存目录不存在"

    video_files = list(cache_dir.glob("*.mp4"))

    if not video_files:
        return "缓存目录中没有视频文件"

    result = ["缓存目录中的视频文件:"]
    for video in sorted(video_files, key=lambda x: x.stat().st_mtime, reverse=True):
        size_mb = video.stat().st_size / (1024 * 1024)
        result.append(f"- {video.name} ({size_mb:.2f} MB)")

    return "\n".join(result)


@mcp.prompt
def video_generation_prompt(text: str) -> str:
    """
    视频生成的提示模板

    Args:
        text: 要生成视频的文本内容

    Returns:
        用于视频生成的提示文本
    """
    return f"""
请使用视频生成工具，根据以下文本生成视频：

文本内容: {text}

建议参数：
- 分镜数: 根据文本长度适当调整，文本较长时建议使用更多分镜
- TTS音量: 默认 1.0，可根据需要调整
"""


def main():
    """MCP 服务器入口点"""
    mcp.run()


if __name__ == "__main__":
    main()
