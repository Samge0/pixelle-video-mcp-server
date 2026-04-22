"""
自动视频生成器 - 精简版
用 Playwright 自动化操作 Streamlit 应用
"""
import asyncio
import argparse
import logging
import os
from pathlib import Path
from playwright.async_api import async_playwright
import time
from datetime import datetime

# 设置日志
logger = logging.getLogger(__name__)

# 配置日志处理器
def _setup_logger():
    """配置日志记录器，使用进程 ID 区分不同客户端实例"""
    log_dir = Path(__file__).parent / ".logs"
    log_dir.mkdir(exist_ok=True)
    # 使用进程 ID 作为日志文件名，避免多客户端冲突
    pid = os.getpid()
    log_file = log_dir / f"video_server_{pid}.log"

    # 只在没有 handler 时添加
    if not logger.handlers:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False

_setup_logger()


def generate_filename(text: str, original_filename: str) -> str:
    """
    生成带时间戳和文本前缀的文件名

    格式: {年月日时分秒}_{文本的前20个字}_{原始文件名}

    Args:
        text: 输入的文本内容
        original_filename: 原始文件名

    Returns:
        新的文件名
    """
    # 生成时间戳 (YYYYMMDD_HHMMSS)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 获取文本前20个字符
    text_prefix = text[:20] if len(text) >= 20 else text

    # 组合文件名
    name_without_ext = original_filename.replace('.mp4', '')
    new_filename = f"{timestamp}_{text_prefix}_{name_without_ext}.mp4"

    return new_filename


async def generate_video(text: str, slider_value: int, tts_volume: float, url: str = "http://localhost:58501/", headless: bool = False, timeout: int = 1200):
    """
    执行视频生成流程

    Args:
        text: 输入的文本内容
        slider_value: 分镜滑块值 (5-30)
        tts_volume: TTS音量值 (0.1-5.0)
        url: 目标 URL
        headless: 是否无头模式
        timeout: 等待超时时间（秒），默认 1200 (20分钟)
    """
    async with async_playwright() as p:
        msg = f"[1/4] 启动浏览器访问 {url}"
        logger.info(msg)
        print(msg)
        browser = await p.chromium.launch(headless=headless)
        # 设置浏览器语言为中文
        context = await browser.new_context(locale="zh-CN")
        page = await context.new_page()
        await page.goto(url, wait_until="networkidle")

        # 切换到中文
        msg = "  切换语言到中文..."
        logger.info(msg)
        print(msg)
        try:
            lang_input = await page.wait_for_selector('input[aria-label*="Language"]', timeout=5000)
            await lang_input.click()
            await asyncio.sleep(0.3)
            zh_option = await page.wait_for_selector('[role="option"]:has-text("简体中文")', timeout=2000)
            await zh_option.click()
            await asyncio.sleep(0.5)
            msg = "  ✓ 语言已切换为中文"
            logger.info(msg)
            print(msg)
        except Exception as e:
            msg = f"  ⚠ 语言切换失败，继续使用当前语言: {e}"
            logger.warning(msg)
            print(msg)

        msg = f"[2/4] 输入文本: {text}"
        logger.info(msg)
        print(msg)
        textarea = await page.wait_for_selector('textarea[aria-label="文本输入"]')
        await textarea.fill(text)

        msg = f"[3/4] 设置滑块值为: {slider_value}"
        logger.info(msg)
        print(msg)
        slider = await page.wait_for_selector('div[role="slider"][aria-label="分镜数"]')

        # 找到滑块的轨道（滑块的父元素）
        track = await slider.evaluate_handle('el => el.parentElement')
        track_box = await track.bounding_box()

        # 计算轨道上的目标位置 (滑块范围 3-30)
        percentage = (slider_value - 3) / (30 - 3)
        target_x = track_box['x'] + (track_box['width'] * percentage)
        target_y = track_box['y'] + (track_box['height'] / 2)

        # 点击轨道设置滑块值
        await page.mouse.click(target_x, target_y)
        await asyncio.sleep(0.5)

        # 验证滑块值是否设置成功
        actual_value = await slider.get_attribute('aria-valuenow')
        msg = f"      滑块当前值: {actual_value}"
        logger.info(msg)
        print(msg)

        # 设置TTS音量
        msg = f"      设置TTS音量为: {tts_volume:.1f}x"
        logger.info(msg)
        print(msg)
        try:
            tts_slider = await page.wait_for_selector('div[role="slider"][aria-label="TTS音量"]', timeout=2000)
            track = await tts_slider.evaluate_handle('el => el.parentElement')
            track_box = await track.bounding_box()

            percentage = (tts_volume - 0.1) / (5.0 - 0.1)
            target_x = track_box['x'] + (track_box['width'] * percentage)
            target_y = track_box['y'] + (track_box['height'] / 2)

            await page.mouse.click(target_x, target_y)
            await asyncio.sleep(0.3)

            actual = float(await tts_slider.get_attribute('aria-valuenow'))
            msg = f"      ✓ TTS音量设置完成: {actual:.1f}x"
            logger.info(msg)
            print(msg)
        except Exception as e:
            msg = f"      ⚠ TTS音量设置失败: {e}"
            logger.warning(msg)
            print(msg)

        msg = "[4/4] 点击生成视频按钮"
        logger.info(msg)
        print(msg)
        button = await page.wait_for_selector('button[data-testid="stBaseButton-primary"]:has-text("生成视频")')
        await button.click()
        msg = "✓ 按钮已点击，等待视频生成..."
        logger.info(msg)
        print(msg)

        # 等待并下载视频
        timeout_minutes = timeout / 60
        msg = f"\n等待视频生成（最长{timeout_minutes:.0f}分钟）..."
        logger.info(msg)
        print(msg)
        downloaded_files = []

        start_time = time.time()

        while time.time() - start_time < timeout:
            # 检查是否有 video 元素
            video_elements = await page.query_selector_all('video[data-testid="stVideo"][src*=".mp4"]')

            if video_elements:
                msg = f"\n找到 {len(video_elements)} 个视频"
                logger.info(msg)
                print(msg)

                for i, video in enumerate(video_elements):
                    src = await video.get_attribute('src')

                    if not src:
                        continue

                    # 从 URL 中提取原始文件名
                    original_filename = src.split('/')[-1]
                    if not original_filename.endswith('.mp4'):
                        original_filename = f'video_{i}.mp4'

                    # 生成新文件名: {时间}_{文本前20字}_{原始文件名}
                    filename = generate_filename(text, original_filename)

                    msg = f"  视频URL: {src}"
                    logger.info(msg)
                    print(msg)
                    msg = f"  保存为: {filename}"
                    logger.info(msg)
                    print(msg)

                    # 下载视频
                    try:
                        # 构建完整 URL（如果是相对路径）
                        if src.startswith('/'):
                            full_url = f"{url.rstrip('/')}{src}"
                        elif src.startswith('http'):
                            full_url = src
                        else:
                            full_url = f"{url.rstrip('/')}/{src}"

                        # 使用 page 的 API 下载
                        response = await page.request.get(full_url)
                        content = await response.body()

                        # 保存到项目根目录下的 .cache/videos 目录
                        project_root = Path(__file__).parent
                        cache_dir = project_root / ".cache" / "videos"
                        cache_dir.mkdir(parents=True, exist_ok=True)
                        save_path = cache_dir / filename
                        with open(save_path, 'wb') as f:
                            f.write(content)

                        downloaded_files.append(str(save_path))
                        msg = f"  ✓ 下载完成: {save_path}"
                        logger.info(msg)
                        print(msg)
                    except Exception as e:
                        msg = f"  ✗ 下载失败: {e}"
                        logger.error(msg)
                        print(msg)

                if downloaded_files:
                    msg = f"\n✓ 下载完成: {len(downloaded_files)} 个文件"
                    logger.info(msg)
                    print(msg)
                    for f in downloaded_files:
                        msg = f"  - {Path(f).name}"
                        logger.info(msg)
                        print(msg)
                    break

            await asyncio.sleep(3)

        if not downloaded_files:
            msg = "\n✗ 超时：未检测到视频文件"
            logger.warning(msg)
            print(msg)

        await browser.close()
        return downloaded_files


async def main():
    parser = argparse.ArgumentParser(description="自动视频生成器")
    parser.add_argument("-t", "--text", required=True, help="要输入的文本内容")
    parser.add_argument("-s", "--slider", type=int, default=5, choices=range(5, 31),
                       help="分镜数滑块值 (5-30), 默认: 5")
    parser.add_argument("-v", "--volume", type=float, default=1.0,
                       help="TTS音量值 (0.1-5.0), 默认: 1.0")
    parser.add_argument("-u", "--url", default="http://localhost:58501/",
                       help="目标URL")
    parser.add_argument("--headless", action="store_true", help="无头模式")
    parser.add_argument("--timeout", type=int, default=1200,
                       help="等待视频生成的超时时间（秒），默认: 1200 (20分钟)")

    args = parser.parse_args()

    # 验证TTS音量范围
    if not 0.1 <= args.volume <= 5.0:
        print("错误: TTS音量值必须在 0.1-5.0 之间")
        return

    await generate_video(
        text=args.text,
        slider_value=args.slider,
        tts_volume=args.volume,
        url=args.url,
        headless=args.headless,
        timeout=args.timeout
    )


if __name__ == "__main__":
    asyncio.run(main())
