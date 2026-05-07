import AppKit
import XCTest
@testable import SlapPaper

// MARK: - MottoStore

@MainActor
final class MottoStoreTests: XCTestCase {

    private var tempDir: URL!

    override func setUp() {
        super.setUp()
        tempDir = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString, isDirectory: true)
    }

    override func tearDown() {
        if let dir = tempDir {
            try? FileManager.default.removeItem(at: dir)
        }
        super.tearDown()
    }

    private func makeStore(content: String? = nil) throws -> MottoStore {
        let mottoURL = tempDir.appendingPathComponent("motto.json")
        if let content {
            try FileManager.default.createDirectory(at: tempDir, withIntermediateDirectories: true)
            try content.write(to: mottoURL, atomically: true, encoding: .utf8)
        }
        return MottoStore(userURL: mottoURL, bundledURL: nil)
    }

    func testAddMottoTrimsAndPersists() throws {
        let store = try makeStore()
        try store.addMotto("  hello world  ")
        store.reloadFromDisk()
        XCTAssertEqual(store.mottos.last, "hello world")
    }

    func testAddEmptyMottoThrows() throws {
        let store = try makeStore()
        XCTAssertThrowsError(try store.addMotto("   "))
    }

    func testUpdateMotto() throws {
        let store = try makeStore(content: "[\"alpha\", \"beta\"]")
        try store.updateMotto(at: 1, text: "gamma")
        XCTAssertEqual(store.mottos, ["alpha", "gamma"])
    }

    func testUpdateOutOfBoundsIsNoop() throws {
        let store = try makeStore(content: "[\"a\"]")
        try store.updateMotto(at: 99, text: "z")
        XCTAssertEqual(store.mottos, ["a"])
    }

    func testDeleteMotto() throws {
        let store = try makeStore(content: "[\"a\", \"b\", \"c\"]")
        try store.deleteMotto(at: 1)
        XCTAssertEqual(store.mottos, ["a", "c"])
    }

    func testDeleteOutOfBoundsIsNoop() throws {
        let store = try makeStore(content: "[\"a\"]")
        try store.deleteMotto(at: 5)
        XCTAssertEqual(store.mottos, ["a"])
    }

    func testInvalidUserFileDoesNotOverwriteOnAdd() throws {
        let store = try makeStore(content: "{ not json")
        XCTAssertThrowsError(try store.addMotto("x"))
        let raw = try String(contentsOf: tempDir.appendingPathComponent("motto.json"), encoding: .utf8)
        XCTAssertTrue(raw.contains("{ not json"))
    }

    func testRuntimeMottosFallsBackOnCorruptFile() throws {
        let store = try makeStore(content: "{ not json")
        let result = store.runtimeMottos()
        XCTAssertFalse(result.isEmpty)
        XCTAssertEqual(result, MottoStore.builtInMottos)
    }

    func testRuntimeMottosReturnsBuiltInWhenEmpty() throws {
        let store = try makeStore(content: "[]")
        XCTAssertEqual(store.runtimeMottos(), MottoStore.builtInMottos)
    }

    func testIndexedMottos() throws {
        let store = try makeStore(content: "[\"a\", \"b\"]")
        let indexed = store.indexedMottos
        XCTAssertEqual(indexed.count, 2)
        XCTAssertEqual(indexed[0].index, 0)
        XCTAssertEqual(indexed[0].text, "a")
        XCTAssertEqual(indexed[1].id, "1:b")
    }
}

// MARK: - TextLayout

final class TextLayoutTests: XCTestCase {

    func testWrapBalancesLines() {
        let font = NSFont.systemFont(ofSize: 14)
        let text = "GitHub 上的 Star 越多，你离真正的代码就越远。"
        let fullWidth = TextLayout.measureText(font: font, text: text)
        let lines = TextLayout.wrapTextLines(text, font: font, maxWidth: max(20, fullWidth * 0.55))
        XCTAssertGreaterThan(lines.count, 1)
        XCTAssertTrue(lines.allSatisfy { $0.trimmingCharacters(in: .whitespaces).count > 1 })
        XCTAssertTrue(lines.dropFirst().allSatisfy { line in
            guard let first = line.first else { return true }
            return !Constants.leadingPunctuation.contains(first)
        })
    }

    func testEmptyTextReturnsEmpty() {
        let font = NSFont.systemFont(ofSize: 14)
        XCTAssertEqual(TextLayout.wrapTextLines("", font: font, maxWidth: 200), [])
        XCTAssertEqual(TextLayout.wrapTextLines("   ", font: font, maxWidth: 200), [])
    }

    func testSingleWordReturnsOneLine() {
        let font = NSFont.systemFont(ofSize: 14)
        let lines = TextLayout.wrapTextLines("Hello", font: font, maxWidth: 9999)
        XCTAssertEqual(lines.count, 1)
        XCTAssertEqual(lines.first, "Hello")
    }

    func testCanBreakBetweenRespectsLeadingPunctuation() {
        XCTAssertFalse(TextLayout.canBreakBetween(text: "你好，世界", index: 2))
        XCTAssertTrue(TextLayout.canBreakBetween(text: "你好世界", index: 2))
    }

    func testMeasureTextNonZero() {
        let font = NSFont.systemFont(ofSize: 14)
        XCTAssertGreaterThan(TextLayout.measureText(font: font, text: "Hello"), 0)
        XCTAssertEqual(TextLayout.measureText(font: font, text: ""), 0)
    }
}

// MARK: - GenerationState

final class GenerationStateTests: XCTestCase {

    func testAutoDebounces() async {
        let state = GenerationState(autoDebounceSeconds: 1.0)
        let t0 = ContinuousClock().now
        let ok1 = await state.beginGeneration(source: .auto, now: t0)
        XCTAssertTrue(ok1)
        await state.finishGeneration()
        let ok2 = await state.beginGeneration(source: .auto, now: t0 + .milliseconds(500))
        XCTAssertFalse(ok2)
        let ok3 = await state.beginGeneration(source: .auto, now: t0 + .seconds(2))
        XCTAssertTrue(ok3)
    }

    func testManualBypassesDebounce() async {
        let state = GenerationState(autoDebounceSeconds: 1.0)
        let t0 = ContinuousClock().now
        let ok1 = await state.beginGeneration(source: .auto, now: t0)
        XCTAssertTrue(ok1)
        await state.finishGeneration()
        let ok2 = await state.beginGeneration(source: .manual, now: t0 + .milliseconds(200))
        XCTAssertTrue(ok2)
    }

    func testInProgressBlocksAll() async {
        let state = GenerationState(autoDebounceSeconds: 1.0)
        let t0 = ContinuousClock().now
        let ok1 = await state.beginGeneration(source: .manual, now: t0)
        XCTAssertTrue(ok1)
        let ok2 = await state.beginGeneration(source: .auto, now: t0 + .seconds(5))
        XCTAssertFalse(ok2)
        let ok3 = await state.beginGeneration(source: .manual, now: t0 + .seconds(5))
        XCTAssertFalse(ok3)
        await state.finishGeneration()
        let ok4 = await state.beginGeneration(source: .manual, now: t0 + .seconds(5))
        XCTAssertTrue(ok4)
    }
}

// MARK: - FinderWatcher

final class FinderWatcherTests: XCTestCase {

    func testStartStopDoesNotCrash() {
        let center = NotificationCenter()
        let watcher = FinderWatcher(notificationCenter: center)
        watcher.start { }
        watcher.stop()
    }

    func testDoubleStartReplacesObserver() {
        let center = NotificationCenter()
        let watcher = FinderWatcher(notificationCenter: center)
        var callCount = 0
        watcher.start { callCount += 1 }
        watcher.start { callCount += 10 }

        center.post(
            name: NSWorkspace.didActivateApplicationNotification,
            object: nil,
            userInfo: nil
        )

        RunLoop.current.run(until: Date().addingTimeInterval(0.1))
        XCTAssertTrue(callCount == 0 || callCount == 10,
                       "Only second handler should fire (or none if userInfo missing)")
    }

    func testIsFinderActivationReturnsFalseForNilUserInfo() {
        XCTAssertFalse(FinderWatcher.isFinderActivation(nil))
    }

    func testIsFinderActivationReturnsFalseForWrongType() {
        let info: [AnyHashable: Any] = [NSWorkspace.applicationUserInfoKey: "not an app"]
        XCTAssertFalse(FinderWatcher.isFinderActivation(info))
    }

    func testIsFinderActivationReturnsFalseForMissingKey() {
        let info: [AnyHashable: Any] = ["other": 42]
        XCTAssertFalse(FinderWatcher.isFinderActivation(info))
    }
}

// MARK: - WallpaperGenerator

final class WallpaperGeneratorTests: XCTestCase {

    func testFontSizeScalesWithHeight() {
        let small = WallpaperGenerator.fontSize(forHeight: 1080)
        let large = WallpaperGenerator.fontSize(forHeight: 2160)
        XCTAssertGreaterThan(large, small)
        XCTAssertGreaterThanOrEqual(small, 96)
    }

    func testFontSizeMinimum() {
        let tiny = WallpaperGenerator.fontSize(forHeight: 100)
        XCTAssertEqual(tiny, 96)
    }

    @MainActor
    func testTargetDimensionsReturnsPositive() {
        let (w, h) = WallpaperGenerator.targetDimensions()
        XCTAssertGreaterThan(w, 0)
        XCTAssertGreaterThan(h, 0)
    }

    func testGenerateThrowsOnEmptyMottos() {
        let gen = WallpaperGenerator()
        XCTAssertThrowsError(try gen.generate(usingMottos: [], dimensions: (1920, 1080)))
    }
}
