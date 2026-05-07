import Foundation

actor GenerationState {
    enum Source: String {
        case auto
        case manual
    }

    private var generationInProgress = false
    private var lastAutoGenerationAt: ContinuousClock.Instant?
    private let debounce: Duration

    init(autoDebounceSeconds: TimeInterval = Constants.autoDebounceSeconds) {
        let ns = Int64((autoDebounceSeconds * 1_000_000_000).rounded())
        self.debounce = .nanoseconds(ns)
    }

    /// - Parameter now: Inject for tests; default uses `ContinuousClock.now`.
    func beginGeneration(source: Source, now: ContinuousClock.Instant? = nil) -> Bool {
        let clock = ContinuousClock()
        let t = now ?? clock.now

        if generationInProgress {
            return false
        }

        if source == .auto, let last = lastAutoGenerationAt {
            if t - last < debounce {
                return false
            }
        }

        generationInProgress = true
        if source == .auto {
            lastAutoGenerationAt = t
        }
        return true
    }

    func finishGeneration() {
        generationInProgress = false
    }
}
