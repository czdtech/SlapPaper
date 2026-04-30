# SlapPaper

SlapPaper 是一个极简的 macOS 托盘工具。

它会在你切回桌面时，随机生成一张黑底白字的“打脸壁纸”，用一句短文案把你从收集癖和伪勤奋里拽回来。

## v1.3.1 

*   **平台定位**：收敛为 `macOS only`。
*   **高保真 UI**：采用原生的毛玻璃材质 (`Vibrancy`)，支持系统级深色/浅色模式自适应。
*   **开机自启**：新增“开机自动运行”选项，支持在应用内直接管理 macOS 登录项。
*   **标准存储**：数据存储路径迁移至标准 macOS 应用目录 `~/Library/Application Support/SlapPaper/`。
*   **健壮性**：
    *   日志自动截断（512KB），防止占用过多磁盘空间。
    *   文案加载失败时使用内置兜底，不再崩溃。
    *   修复了编辑器模式下的全局事件监听器泄露问题。
*   **排版优化**：壁纸尺寸跟随主屏幕分辨率，文案自动平衡换行，避免孤字落行。

## 运行

```bash
# 克隆仓库
git clone https://github.com/czdtech/SlapPaper.git
cd SlapPaper

# 创建并激活虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行程序
python generator.py
```

启动后会出现菜单栏图标：
- 点击图标（"SP" 标志）弹出高保真管理面板。
- 支持在面板内直接新增、编辑、删除文案。
- 勾选“登录时自动启动”可实现开机自启。

## 打包

```bash
pyinstaller SlapPaper.spec
```
产物会出现在 `dist/SlapPaper.app`。

## 自定义文案

你可以直接在面板里管理文案，也可以手动编辑用户目录里的文案库：
`~/Library/Application Support/SlapPaper/motto.json`

首次运行、或者用户文案库不存在时，程序会从应用内置的 `motto.json` 读取初始文案。

## 开发与测试

项目拥有完善的测试覆盖：
```bash
python3 -m unittest discover tests
```

## 技术架构

- **语言**：Python 3.13
- **框架**：PyObjC (AppKit / Foundation)
- **监听**：`NSWorkspace` 事件驱动
- **渲染**：`NSBitmapImageRep` 原生像素级绘制
- **版本控制**：Git
