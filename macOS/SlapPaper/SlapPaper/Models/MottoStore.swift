import Foundation

enum MottoStoreError: LocalizedError {
    case missingFile(URL)
    case invalidJSON(URL)
    case notArray(URL)
    case readFailed(URL, Error)

    var errorDescription: String? {
        switch self {
        case .missingFile(let u): return "Motto file is missing: \(u.path)"
        case .invalidJSON(let u): return "Motto file is invalid JSON: \(u.path)"
        case .notArray(let u): return "Motto file must contain a JSON array: \(u.path)"
        case .readFailed(let u, let e): return "Unable to read motto file: \(u.path) — \(e.localizedDescription)"
        }
    }
}

/// Persists mottos to the same path and format as the Python app: `~/Library/Application Support/SlapPaper/motto.json`
final class MottoStore: ObservableObject {
    @Published private(set) var mottos: [String] = []
    @Published var loadErrorMessage: String?

    private let userURL: URL
    private let bundledURL: URL?

    static let builtInMottos: [String] = [
        "收藏了不代表学会了，那只是你逃避思考的避难所。",
        "你的收藏夹是知识的坟场，不是进化的阶梯。",
        "GitHub 上的 Star 越多，你离真正的代码就越远。",
        "买课带来的成长感是廉价的幻觉，只有敲代码才是痛苦的真实。",
        "工具无法拯救你的平庸，只有产出可以。",
    ]

    init(userURL: URL = Constants.mottoFileURL, bundledURL: URL? = Constants.bundledMottoURL) {
        self.userURL = userURL
        self.bundledURL = bundledURL
        reloadFromDisk()
    }

    /// Mottos for wallpaper generation (runtime): user file → bundled → built-in; invalid user file falls back without overwriting.
    func runtimeMottos() -> [String] {
        let loaded: [String]
        do {
            loaded = try loadMottosForEditor()
        } catch {
            loaded = (try? readMottos(from: bundledURL)) ?? Self.builtInMottos
        }
        return loaded.isEmpty ? Self.builtInMottos : loaded
    }

    /// Loads for editor UI; throws on corrupt user file (matches Python editor behavior).
    func loadMottosForEditor() throws -> [String] {
        if FileManager.default.fileExists(atPath: userURL.path) {
            return try readMottos(from: userURL)
        }
        return try readBundledOrBuiltIn()
    }

    func reloadFromDisk() {
        do {
            mottos = try loadMottosForEditor()
            loadErrorMessage = nil
        } catch {
            mottos = []
            loadErrorMessage = error.localizedDescription
        }
    }

    func addMotto(_ text: String) throws {
        let normalized = Self.normalize(text)
        guard !normalized.isEmpty else {
            throw NSError(domain: "SlapPaper", code: 1, userInfo: [NSLocalizedDescriptionKey: "Motto text cannot be empty."])
        }
        var list = try loadMottosForEditor()
        list.append(normalized)
        try writeMottos(list)
        mottos = list
        loadErrorMessage = nil
    }

    func updateMotto(at index: Int, text: String) throws {
        let normalized = Self.normalize(text)
        guard !normalized.isEmpty else {
            throw NSError(domain: "SlapPaper", code: 1, userInfo: [NSLocalizedDescriptionKey: "Motto text cannot be empty."])
        }
        var list = try loadMottosForEditor()
        guard list.indices.contains(index) else { return }
        list[index] = normalized
        try writeMottos(list)
        mottos = list
        loadErrorMessage = nil
    }

    func deleteMotto(at index: Int) throws {
        var list = try loadMottosForEditor()
        guard list.indices.contains(index) else { return }
        list.remove(at: index)
        try writeMottos(list)
        mottos = list
        loadErrorMessage = nil
    }

    // MARK: - Private

    private func readBundledOrBuiltIn() throws -> [String] {
        if let b = bundledURL {
            do {
                let m = try readMottos(from: b)
                return m.isEmpty ? Self.builtInMottos : m
            } catch {
                return Self.builtInMottos
            }
        }
        return Self.builtInMottos
    }

    private func readMottos(from url: URL?) throws -> [String] {
        guard let url else {
            return Self.builtInMottos
        }
        let data: Data
        do {
            data = try Data(contentsOf: url)
        } catch let e as CocoaError where e.code == .fileReadNoSuchFile {
            throw MottoStoreError.missingFile(url)
        } catch {
            throw MottoStoreError.readFailed(url, error)
        }
        let decoded: Any
        do {
            decoded = try JSONSerialization.jsonObject(with: data)
        } catch {
            throw MottoStoreError.invalidJSON(url)
        }
        guard let arr = decoded as? [Any] else {
            throw MottoStoreError.notArray(url)
        }
        return arr.compactMap { item in
            guard let s = item as? String else { return nil }
            let n = Self.normalize(s)
            return n.isEmpty ? nil : n
        }
    }

    private func writeMottos(_ list: [String]) throws {
        try FileManager.default.createDirectory(at: userURL.deletingLastPathComponent(), withIntermediateDirectories: true)
        let data = try JSONSerialization.data(withJSONObject: list, options: [.prettyPrinted])
        var text = String(data: data, encoding: .utf8) ?? "[]"
        if !text.hasSuffix("\n") {
            text += "\n"
        }
        guard let out = text.data(using: .utf8) else { return }
        try out.write(to: userURL, options: .atomic)
    }

    private static func normalize(_ text: String) -> String {
        text.trimmingCharacters(in: .whitespacesAndNewlines)
    }
}
