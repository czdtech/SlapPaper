import Foundation

enum Constants {
    static let appName = "SlapPaper"
    static let finderBundleID = "com.apple.finder"

    static let defaultWidth = 3840
    static let defaultHeight = 2160

    static let maxTextWidthRatio: CGFloat = 0.8
    static let maxLineCount = 3
    static let lineSpacing: CGFloat = 40
    static let autoDebounceSeconds: TimeInterval = 1.0

    static let fontNames = ["PingFangSC-Regular", "STHeitiSC-Medium"]

    static let leadingPunctuation: Set<Character> = [
        "，", "。", "！", "？", "；", "：", "、", "\u{201D}", "\u{2019}", "）", "》", "】",
        ",", ".", "!", "?", ";", ":", ")", "]", "}",
    ]
    static let wordJoiners: Set<Character> = ["-", "_", ".", "/", "+", "#"]

    static let logMaxBytes = 512 * 1024

    static var storageURL: URL {
        FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
            .appendingPathComponent(appName, isDirectory: true)
    }

    static var mottoFileURL: URL {
        storageURL.appendingPathComponent("motto.json", isDirectory: false)
    }

    static var settingsFileURL: URL {
        storageURL.appendingPathComponent("settings.json", isDirectory: false)
    }

    static var logFileURL: URL {
        storageURL.appendingPathComponent("debug.log", isDirectory: false)
    }

    static var bundledMottoURL: URL? {
        Bundle.main.url(forResource: "motto", withExtension: "json")
    }
}

enum AppLog {
    private static let queue = DispatchQueue(label: "com.slappaper.log")

    private static let formatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "HH:mm:ss"
        return f
    }()

    static func append(_ message: String) {
        let line = "[\(formatter.string(from: Date()))] \(message)\n"
        guard let data = line.data(using: .utf8) else { return }

        queue.async {
            let dir = Constants.storageURL
            try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
            let path = Constants.logFileURL.path

            if FileManager.default.fileExists(atPath: path),
               let attrs = try? FileManager.default.attributesOfItem(atPath: path),
               let size = attrs[.size] as? Int64,
               size > Constants.logMaxBytes {
                trimLog(at: path, keepLast: Constants.logMaxBytes / 2)
            }

            if FileManager.default.fileExists(atPath: path) {
                if let handle = FileHandle(forWritingAtPath: path) {
                    defer { try? handle.close() }
                    _ = try? handle.seekToEnd()
                    try? handle.write(contentsOf: data)
                }
            } else {
                try? data.write(to: URL(fileURLWithPath: path))
            }
        }
    }

    private static func trimLog(at path: String, keepLast: Int) {
        guard let handle = FileHandle(forReadingAtPath: path) else { return }
        defer { try? handle.close() }
        guard let fileSize = try? handle.seekToEnd() else { return }
        let keep = UInt64(max(0, keepLast))
        let start = fileSize > keep ? (fileSize - keep) : 0
        try? handle.seek(toOffset: start)
        guard let tail = try? handle.readToEnd() else { return }
        let data = tail.drop { byte in byte != UInt8(ascii: "\n") }
        try? Data(data).write(to: URL(fileURLWithPath: path))
    }
}
