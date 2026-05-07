import AppKit
import XCTest
@testable import SlapPaper

final class MottoStoreTests: XCTestCase {

    func testAddMottoTrimsAndPersists() throws {
        let dir = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString, isDirectory: true)
        let mottoURL = dir.appendingPathComponent("motto.json")
        let store = MottoStore(userURL: mottoURL, bundledURL: nil)

        try store.addMotto("  hello world  ")
        store.reloadFromDisk()
        XCTAssertEqual(store.mottos.last, "hello world")
    }

    func testInvalidUserFileDoesNotOverwriteOnAdd() throws {
        let dir = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString, isDirectory: true)
        let mottoURL = dir.appendingPathComponent("motto.json")
        try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        try "{ not json".write(to: mottoURL, atomically: true, encoding: .utf8)
        let store = MottoStore(userURL: mottoURL, bundledURL: nil)

        XCTAssertThrowsError(try store.addMotto("x"))
        let raw = try String(contentsOf: mottoURL, encoding: .utf8)
        XCTAssertTrue(raw.contains("{ not json"))
    }
}

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
}

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
        await state.finishGeneration()
    }
}

final class FinderWatcherSmokeTests: XCTestCase {

    func testStartStopDoesNotCrash() {
        let center = NotificationCenter()
        let watcher = FinderWatcher(notificationCenter: center)
        watcher.start { }
        watcher.stop()
    }
}
