# SlapPaper

SlapPaper 是一个极简的 macOS 托盘工具。

它会在你切回桌面时，随机生成一张黑底白字的“打脸壁纸”，用一句短文案把你从收集癖和伪勤奋里拽回来。

## v1.3

- 平台定位收敛为 `macOS only`
- 文案加载失败时使用内置兜底，不再静默崩掉后台线程
- 壁纸尺寸改为跟随主屏幕分辨率
- 文案换行改为平衡排版，避免孤字和标点单独落行
- 自动触发改为 `Finder 激活即换壁纸`
- 前台监听改为 `NSWorkspace` 事件驱动，不再依赖轮询
- 项目结构拆分为 `app / tray / listener / generator / editor / store / state / config`
- 菜单栏图标点击后会弹出一个原生 `AppKit` 文案管理面板
- 支持直接在应用内增删改文案，并即时影响后续生成结果
- 用户文案库持久化到 `~/Library/Application Support/SlapPaper/motto.json`
- 文案库 JSON 损坏时，编辑器会报错而不是把默认文案覆盖回去

## 运行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python generator.py
```

启动后会出现菜单栏图标：

- 点击图标会弹出文案管理面板
- 面板顶部可以新增文案
- 面板列表里每条文案都支持 `编辑 / 删除`
- 面板底部保留 `刷新壁纸` 和 `退出`

自动触发规则：

- 只有在应用启动后，Finder 被激活时才会自动换壁纸
- 启动时如果前台刚好就是 Finder，不会立即自动换
- 自动触发有一个很短的内部防抖，用来避免系统重复通知

## 打包

```bash
pyinstaller SlapPaper.spec
```

产物会出现在 `dist/SlapPaper.app`。

## 自定义文案

你可以直接在面板里管理文案，也可以手动编辑用户目录里的文案库：

```bash
~/Library/Application\ Support/SlapPaper/motto.json
```

首次运行、或者用户文案库不存在时，程序会从应用内置的 `motto.json` 读取初始文案。

文件格式示例：

```json
[
  "收藏了不代表学会了，那只是你逃避思考的避难所。",
  "你的收藏夹是知识的坟场，不是进化的阶梯。"
]
```

如果用户文案库缺失，程序会自动回退到内置文案集。

如果用户文案库格式损坏：

- 壁纸生成会临时回退到内置文案集，避免应用失效
- 编辑器不会拿默认文案覆盖你的坏文件
- 修好 JSON 后，重新打开面板或重启应用即可继续使用
