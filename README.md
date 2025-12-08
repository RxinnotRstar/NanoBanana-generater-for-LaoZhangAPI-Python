# Gemini AI（Nano banana）图像生成器 - 老张API专版

一款基于 tkinter 的应用程序，通过 Nano Banana API （老张API）调用 Google Gemini 模型生成图像。支持参考图上传、多分辨率选择和实时界面缩放。

我的邀请链接：https://api.laozhang.ai/register/?aff_code=EVOV

## 主要特性

- **双模型支持**：Gemini 2.5 Flash (稳定版) 和 Gemini 3 Pro (最新版)
- **多分辨率输出**：1K、2K、4K (Gemini 3 Pro 专属)
- **参考图功能**：最多支持 14 张参考图片
- **实时预览**：生成图片自适应窗口大小，无裁剪显示
- **原始数据查看**：支持查看和保存完整 API 响应
- **智能日志**：可选的 JSON 格式日志记录
- **界面缩放**：75%-300% 八档缩放

## 系统要求

- Python 3.7+
- Windows 10/11 (推荐) / Linux / macOS
- 网络连接 (需访问 `api.laozhang.ai`)

## 安装步骤

```bash
# 克隆或下载代码
git clone [repository-url]

# 安装依赖
pip install requests pillow

# 可选但推荐的剪贴板支持
pip install pyperclip
```

## 配置 API 密钥

1. 获取 API 密钥：访问老张 API 平台注册账号，配置并获取API密钥（我的邀请链接：https://api.laozhang.ai/register/?aff_code=EVOV）
2. 启动程序后，在"API配置"区域输入密钥

## 使用方法

### 基本生成流程

1. **填写提示词**：在提示词文本框中输入描述
2. **选择模型**：Gemini 3 Pro 支持更高分辨率和更好的出图效果
3. **设置参数**：
   - 纵横比：21:9, 16:9, 4:3, 1:1, 9:16 等（仅 Gemini 3）
   - 分辨率：根据模型自动切换可用选项
4. **添加参考图** (可选)：
   - 点击"添加图片"选择最多14张参考图
   - 点击图片右上角 × 删除单张
5. **生成图片**：点击"生成图片"按钮
6. **保存结果**：
   - 点击"保存图片"导出 PNG
   - 点击"保存原始JSON"导出完整响应（不含Base64）

### 界面缩放

- 顶部缩放控件支持 75%-300% 八档调节
- 自动记忆所有状态 (提示词、图片、日志设置等)
- 调整缩放后无需重新生成图片

### 日志功能

启用"保存日志到文件"后，所有操作会记录在 `logs/` 目录：

- 成功日志：`gemini_YYYYMMDD_HHMMSS_success.log`
- 错误日志：`gemini_YYYYMMDD_HHMMSS_error.log`
- 保存日志：`gemini_YYYYMMDD_HHMMSS_save.log`

日志包含完整请求参数和响应数据。

## 参数说明

| 参数 | 说明 | 限制 |
|------|------|------|
| API密钥 | Nano Banana 平台授权密钥 | 必填 |
| 提示词 | 图像描述文本 | 最多 2000 字符 |
| 参考图 | 风格/内容参考图片 | ≤14 张，每张 ≤10MB |
| 网络超时 | API 请求超时时间 | 0=无限制，默认 1200 秒 |

## 注意事项

⚠️ **重要提示**

- 生成失败时请检查安全评级 (safetyRatings) 和完成原因 (finishReason)
- 大分辨率图片生成时间较长，建议设置充足的超时时间
- 日志文件可能包含 API 密钥，请妥善保管

## 故障排除

**问图片生成失败**

1. 检查 API 密钥是否有效
2. 确认提示词未触发安全过滤器
3. 查看"原始响应"标签页的错误信息
4. 尝试切换回稳定版模型

**界面显示异常**

1. 重置缩放至 100%
2. 检查系统 DPI 设置
3. 确保所有依赖已正确安装

**无法复制图片**

- 安装 `pyperclip` 库获得完整支持
- 或手动保存图片后使用系统工具复制

## 版本信息

- **API 端点**：`https://api.laozhang.ai/v1beta/models/`
- **脚本支持模型**：`gemini-2.5-flash-image`, `gemini-3-pro-image-preview`
