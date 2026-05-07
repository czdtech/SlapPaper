# SlapPaper (Swift / macOS 13+)

Native Swift + SwiftUI 实现，与根目录 Python 版共用同一数据目录：

- `~/Library/Application Support/SlapPaper/motto.json`
- `~/Library/Application Support/SlapPaper/settings.json`（首次启动会迁移其中的 `autostart` 到 `UserDefaults`）
- `~/Library/Application Support/SlapPaper/debug.log`
- 壁纸 PNG：`slappaper_*.png` 同上目录

## 构建与运行

1. 用 **Xcode**（需完整 Xcode，非仅 Command Line Tools）打开 `SlapPaper.xcodeproj`。
2. 选择 Scheme **SlapPaper**，Run。
3. 菜单栏出现引用图标；点「文案库…」打开管理窗口。

## 测试

```bash
xcodebuild -scheme SlapPaper -destination 'platform=macOS' test
```

## 与 Python 版的差异

- 登录项使用 `SMAppService`（系统「登录项」），不再依赖 `osascript`。
- 菜单栏使用 `MenuBarExtra`；文案面板为独立 `NSWindow` + SwiftUI（兼容 macOS 13，未使用仅 macOS 14+ 的 `menuBarExtraStyle(.window)`）。
- 最低系统：macOS 13 Ventura。
