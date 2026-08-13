# Pixelle Video MCP Server

基于 FastMCP 的视频生成 MCP 服务器，使用 Playwright 自动化操作 [Pixelle-Video](https://github.com/AIDC-AI/Pixelle-Video) 应用生成视频。


> 🌐 **[在线宣传页](https://samge0.github.io/pixelle-video-mcp-server/)** — 可视化了解功能特性与工作流程

## 安装

1. 安装 Python 依赖:
```bash
pip install -r requirements.txt
```

2. 安装 Playwright 浏览器:
```bash
playwright install chromium
```

## 使用

### 作为独立脚本使用

```bash
python generate_video.py -t "你的文本内容" -s 5 -v 1.0
```

参数说明:
- `-t, --text`: 要输入的文本内容（必需）
- `-s, --slider`: 分镜滑块值 (5-30)，默认 5
- `-v, --volume`: TTS音量值 (0.1-5.0)，默认 1.0
- `-u, --url`: Streamlit 应用 URL，默认 http://localhost:58501/
- `--headless`: 无头模式运行浏览器
- `--timeout`: 超时时间（秒），默认 600

## MCP 工具

### generate_video_tool

自动生成视频。

参数:
- `text` (str): 要输入的文本内容
- `slider_value` (int): 分镜滑块值 (5-30)，默认 5
- `tts_volume` (float): TTS音量值 (0.1-5.0)，默认 1.0
- `url` (str): Streamlit 应用 URL，默认 http://localhost:58501/
- `headless` (bool): 是否使用无头模式，默认 False
- `timeout` (int): 超时时间（秒），默认 600

返回: 下载的视频文件路径列表

### Resources

- `cache://videos`: 获取缓存目录中的所有视频文件列表

### Prompts

- `video_generation_prompt`: 视频生成的提示模板

## 配置 Claude Desktop

在 Claude Desktop 的配置文件中添加:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "pixelle-video-server": {
      "command": "python",
      "args": ["{your_dir_path}/pixelle-video-server/server.py"]
    }
  }
}
```

## 交互方式

```text
示例1：
生成视频，文本：如果防止上头，分镜数5，音量调到5倍

示例2：
生成视频，文本：哪些人会孤独终老，分镜数5，音量调到5倍，无头模式
```

## 输出

生成的视频文件会保存到 `.cache/videos/` 目录，文件名格式为:
`{时间戳}_{文本前20字}_{原始文件名}.mp4`

例如: `20250415_143022_这是一段测试文本_video_0.mp4`

## 相关截图
<img width="783" height="496" alt="image" src="https://github.com/user-attachments/assets/fb302d3e-f09f-48ca-9427-bd5d60dc7283" />

<img width="1139" height="679" alt="image" src="https://github.com/user-attachments/assets/9c77616a-330e-4859-b8e4-052a4dc40ef5" />



https://github.com/user-attachments/assets/2d23b2dc-8068-430f-bc57-f44362c9291a

<img width="1098" height="607" alt="image" src="https://github.com/user-attachments/assets/96f96b56-24f4-431a-af34-fbb10f2b889b" />



https://github.com/user-attachments/assets/bca2cd60-5c22-45fc-9405-957bfb2bbaf3





