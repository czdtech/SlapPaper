import AppKit
import Foundation

final class WallpaperGenerator: @unchecked Sendable {

    private var cachedFont: NSFont?
    private var cachedFontSize: CGFloat = 0
    private var cachedMottos: [String] = []

    func loadResources(mottos: [String], dimensions: (Int, Int)? = nil, force: Bool = false) {
        let (_, h) = dimensions ?? Self.targetDimensions()
        let targetSize = Self.fontSize(forHeight: h)

        if !force,
           cachedFont != nil,
           !cachedMottos.isEmpty,
           cachedFontSize == targetSize {
            return
        }

        AppLog.append("Loading resources...")
        cachedMottos = mottos
        cachedFontSize = targetSize
        cachedFont = Self.loadFont(size: targetSize)
    }

    /// - Parameter dimensions: Pass screen size from the main thread; if `nil`, reads `NSScreen` on the current thread.
    func generate(usingMottos mottos: [String], dimensions: (Int, Int)? = nil) throws -> String {
        guard !mottos.isEmpty else {
            throw NSError(domain: "SlapPaper", code: 2, userInfo: [NSLocalizedDescriptionKey: "No mottos available for rendering."])
        }

        loadResources(mottos: mottos, dimensions: dimensions)
        guard let font = cachedFont else {
            throw NSError(domain: "SlapPaper", code: 3, userInfo: [NSLocalizedDescriptionKey: "Font unavailable."])
        }

        let (width, height) = dimensions ?? Self.targetDimensions()
        let text = mottos.randomElement()!
        try Self.cleanupPreviousWallpapers()

        let stamp = Int(Date().timeIntervalSince1970)
        let outputURL = Constants.storageURL.appendingPathComponent("slappaper_\(stamp).png", isDirectory: false)

        let maxTextWidth = CGFloat(width) * Constants.maxTextWidthRatio
        let lines = TextLayout.wrapTextLines(text, font: font, maxWidth: maxTextWidth)
        let wrapped = lines.joined(separator: "\n")

        try renderWallpaper(text: wrapped, width: width, height: height, font: font, to: outputURL)
        try setWallpaper(url: outputURL)

        AppLog.append("Wallpaper ready: \(String(text.prefix(24)))...")
        return outputURL.path
    }

    // MARK: - Dimensions & font

    static func targetDimensions() -> (Int, Int) {
        guard let screen = NSScreen.main ?? NSScreen.screens.first else {
            return (Constants.defaultWidth, Constants.defaultHeight)
        }
        let frame = screen.frame
        let scale = screen.backingScaleFactor
        let w = max(1, Int((frame.width * scale).rounded()))
        let h = max(1, Int((frame.height * scale).rounded()))
        return (w, h)
    }

    static func fontSize(forHeight h: Int) -> CGFloat {
        max(96, CGFloat(h) * 0.074)
    }

    private static func loadFont(size: CGFloat) -> NSFont {
        for name in Constants.fontNames {
            if let f = NSFont(name: name, size: size) {
                return f
            }
        }
        AppLog.append("Falling back to NSFont.systemFontOfSize.")
        return NSFont.systemFont(ofSize: size)
    }

    // MARK: - Files

    private static func cleanupPreviousWallpapers() throws {
        let dir = Constants.storageURL
        try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        let urls = try FileManager.default.contentsOfDirectory(at: dir, includingPropertiesForKeys: nil)
        for url in urls where url.lastPathComponent.hasPrefix("slappaper_") && url.pathExtension.lowercased() == "png" {
            try? FileManager.default.removeItem(at: url)
        }
    }

    // MARK: - Render

    private func renderWallpaper(text: String, width: Int, height: Int, font: NSFont, to url: URL) throws {
        guard let rep = NSBitmapImageRep(
            bitmapDataPlanes: nil,
            pixelsWide: width,
            pixelsHigh: height,
            bitsPerSample: 8,
            samplesPerPixel: 4,
            hasAlpha: true,
            isPlanar: false,
            colorSpaceName: .deviceRGB,
            bytesPerRow: 0,
            bitsPerPixel: 0
        ) else {
            throw NSError(domain: "SlapPaper", code: 4, userInfo: [NSLocalizedDescriptionKey: "Failed to allocate NSBitmapImageRep."])
        }

        NSGraphicsContext.saveGraphicsState()
        defer { NSGraphicsContext.restoreGraphicsState() }

        guard let ctx = NSGraphicsContext(bitmapImageRep: rep) else {
            throw NSError(domain: "SlapPaper", code: 5, userInfo: [NSLocalizedDescriptionKey: "Failed to create graphics context."])
        }
        NSGraphicsContext.current = ctx

        NSColor.black.setFill()
        NSBezierPath(rect: NSRect(x: 0, y: 0, width: width, height: height)).fill()

        let paragraph = NSMutableParagraphStyle()
        paragraph.alignment = .center
        paragraph.lineSpacing = Constants.lineSpacing

        let attrs: [NSAttributedString.Key: Any] = [
            .font: font,
            .foregroundColor: NSColor.white,
            .paragraphStyle: paragraph,
        ]

        let s = text as NSString
        let bounds = s.boundingRect(
            with: NSSize(width: CGFloat(width), height: CGFloat(height)),
            options: [.usesLineFragmentOrigin],
            attributes: attrs
        )
        let textHeight = bounds.height
        let rect = NSRect(x: 0, y: (CGFloat(height) - textHeight) / 2, width: CGFloat(width), height: textHeight)
        s.draw(with: rect, options: [.usesLineFragmentOrigin], attributes: attrs)

        guard let data = rep.representation(using: .png, properties: [:]) else {
            throw NSError(domain: "SlapPaper", code: 6, userInfo: [NSLocalizedDescriptionKey: "Failed to encode PNG data."])
        }
        try data.write(to: url, options: .atomic)
    }

    private func setWallpaper(url: URL) throws {
        let screens = NSScreen.screens
        guard !screens.isEmpty else {
            throw NSError(domain: "SlapPaper", code: 7, userInfo: [NSLocalizedDescriptionKey: "No screens detected; cannot set wallpaper."])
        }
        var failures = 0
        for screen in screens {
            do {
                try NSWorkspace.shared.setDesktopImageURL(url, for: screen, options: [:])
            } catch {
                failures += 1
                AppLog.append("setDesktopImageURL failed on one screen: \(error.localizedDescription)")
            }
        }
        if failures == screens.count {
            throw NSError(domain: "SlapPaper", code: 8, userInfo: [NSLocalizedDescriptionKey: "Failed to set wallpaper on all screens."])
        }
    }
}
