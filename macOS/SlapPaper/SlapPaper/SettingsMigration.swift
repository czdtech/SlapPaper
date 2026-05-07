import Foundation

/// One-time migration from Python `settings.json` (`autostart` key) into `UserDefaults`.
enum SettingsMigration {
    private static let migratedKey = "settingsMigratedFromJSON"
    private static let autostartKey = "autostart"

    static func runIfNeeded() {
        let defaults = UserDefaults.standard
        guard !defaults.bool(forKey: migratedKey) else { return }

        defer { defaults.set(true, forKey: migratedKey) }

        guard FileManager.default.fileExists(atPath: Constants.settingsFileURL.path) else { return }
        guard let data = try? Data(contentsOf: Constants.settingsFileURL),
              let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let v = obj[autostartKey] as? Bool else { return }

        defaults.set(v, forKey: autostartKey)
    }
}
