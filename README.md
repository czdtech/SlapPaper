# SlapPaper

SlapPaper 是一个极简的 macOS 菜单栏工具。

切回桌面时，它会自动生成一张黑底白字的"打脸壁纸"——用一句短文案把你从收藏癖和伪勤奋里拽回来。

## 功能

- 切换到 Finder 时自动刷新壁纸
- 菜单栏一键手动刷新
- 内置文案库管理面板（增删改）
- 开机自动启动（系统登录项）
- 文案自动平衡换行，避免孤字落行
- 壁纸尺寸跟随主屏幕物理分辨率

## 系统要求

- macOS 13 (Ventura) 或更高
- Xcode 15+（仅构建时需要）

## 安装与使用

### 方式一：Xcode 构建运行（推荐开发时）

```bash
git clone https://github.com/czdtech/SlapPaper.git
cd SlapPaper
open SlapPaper.xcodeproj
```

在 Xcode 中选择 Scheme **SlapPaper** → 点击 **Run**（⌘R）。

### 方式二：命令行构建

```bash
# 构建 Release 版本
xcodebuild -scheme SlapPaper -configuration Release -derivedDataPath build

# 生成的 .app 在这里
open build/Build/Products/Release/SlapPaper.app
```

如需长期使用，可将 `SlapPaper.app` 拖入 `/Applications` 目录。

### 方式三：Archive 导出（分发用）

1. Xcode → Product → Archive
2. Distribute App → Copy App
3. 将导出的 `SlapPaper.app` 拷贝到 `/Applications`

## 使用方法

启动后菜单栏出现 **❝** 图标：

| 操作 | 说明 |
|------|------|
| 点击「文案库…」 | 打开管理面板，增删改文案 |
| 点击「刷新壁纸」 | 立即随机生成新壁纸 |
| 点击「退出」 | 退出应用 |

文案存储在 `~/Library/Application Support/SlapPaper/motto.json`，也可以直接编辑这个 JSON 文件。

## 测试

```bash
xcodebuild -scheme SlapPaper -destination 'platform=macOS' test
```

## 技术架构

- **语言**：Swift 5 + SwiftUI
- **菜单栏**：`MenuBarExtra`（macOS 13+）
- **登录项**：`SMAppService`（系统级登录项管理）
- **监听**：`NSWorkspace` 通知驱动
- **渲染**：`NSBitmapImageRep` 原生像素级绘制
- **排版**：动态规划算法实现平衡换行
- **并发**：Swift `actor` + `Task.detached` 隔离渲染线程

## 项目结构

```
SlapPaper/
├── SlapPaperApp.swift        # 入口，MenuBarExtra 定义
├── AppController.swift       # 主控制器，串联各模块
├── Constants.swift           # 全局常量 + AppLog 日志
├── SettingsMigration.swift   # Python 版设置迁移
├── Models/
│   ├── MottoStore.swift      # 文案持久化（JSON）
│   └── GenerationState.swift # 生成状态机（actor）
├── Services/
│   ├── TextLayout.swift      # DP 平衡换行算法
│   ├── WallpaperGenerator.swift  # 壁纸渲染引擎
│   └── FinderWatcher.swift   # Finder 激活监听
├── Views/
│   └── MottoEditorView.swift # 文案管理 SwiftUI 界面
└── Resources/
    └── motto.json            # 内置默认文案
```
