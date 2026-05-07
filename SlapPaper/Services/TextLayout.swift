import AppKit
import Foundation

enum TextLayout {

    static func wrapTextLines(
        _ text: String,
        font: NSFont,
        maxWidth: CGFloat,
        maxLines: Int = Constants.maxLineCount
    ) -> [String] {
        let cleaned = text.split(whereSeparator: \.isWhitespace).joined(separator: " ")
        guard !cleaned.isEmpty else { return [] }

        let breakPoints = breakIndices(for: String(cleaned))

        struct CacheKey: Hashable {
            let startIndex: Int
            let linesLeft: Int
        }
        var memo: [CacheKey: (CGFloat, [String])?] = [:]

        func solve(startIndex: Int, linesLeft: Int) -> (CGFloat, [String])? {
            let key = CacheKey(startIndex: startIndex, linesLeft: linesLeft)
            if let cached = memo[key] { return cached }

            var best: (CGFloat, [String])?

            for endIndex in breakPoints where endIndex > startIndex {
                let segment = String(cleaned[cleaned.index(cleaned.startIndex, offsetBy: startIndex)..<cleaned.index(cleaned.startIndex, offsetBy: endIndex)])
                    .trimmingCharacters(in: .whitespaces)
                guard !segment.isEmpty else { continue }

                let width = measureText(font: font, text: segment)
                if width > maxWidth { continue }

                let isLastLine = endIndex == cleaned.count
                if !isLastLine && linesLeft == 1 { continue }

                let candidatePenalty = linePenalty(segment: segment, width: width, maxWidth: maxWidth, isLastLine: isLastLine)

                let candidate: (CGFloat, [String])
                if isLastLine {
                    candidate = (candidatePenalty, [segment])
                } else {
                    guard let rest = solve(startIndex: endIndex, linesLeft: linesLeft - 1) else { continue }
                    candidate = (candidatePenalty + rest.0, [segment] + rest.1)
                }

                if best == nil || candidate.0 < best!.0 {
                    best = candidate
                }
            }

            memo[key] = best
            return best
        }

        var bestSolution: (CGFloat, [String])?
        for lineCount in 1...maxLines {
            guard let candidate = solve(startIndex: 0, linesLeft: lineCount) else { continue }
            if bestSolution == nil || candidate.0 < bestSolution!.0 {
                bestSolution = candidate
            }
        }

        if let lines = bestSolution?.1 {
            return lines
        }
        return [cleaned]
    }

    private static func breakIndices(for text: String) -> [Int] {
        var pts = [0]
        for i in 1..<text.count {
            if canBreakBetween(text: text, index: i) {
                pts.append(i)
            }
        }
        pts.append(text.count)
        return pts
    }

    static func canBreakBetween(text: String, index: Int) -> Bool {
        guard index > 0, index < text.count else { return true }
        let idx = text.index(text.startIndex, offsetBy: index)
        let prev = text[text.index(before: idx)]
        let cur = text[idx]

        if Constants.leadingPunctuation.contains(cur) {
            return false
        }

        if prev.isWhitespace || cur.isWhitespace {
            return true
        }

        let prevIsWord = prev.isASCII && (prev.isLetter || prev.isNumber || Constants.wordJoiners.contains(prev))
        let curIsWord = cur.isASCII && (cur.isLetter || cur.isNumber || Constants.wordJoiners.contains(cur))
        return !(prevIsWord && curIsWord)
    }

    private static func linePenalty(segment: String, width: CGFloat, maxWidth: CGFloat, isLastLine: Bool) -> CGFloat {
        let visibleLength = segment.replacingOccurrences(of: " ", with: "").count
        let slack = maxWidth - width
        var penalty = slack * slack

        if isLastLine {
            penalty *= 0.35
            if visibleLength <= 2 {
                penalty += maxWidth * maxWidth
            }
        } else if visibleLength <= 1 {
            penalty += maxWidth * maxWidth
        }
        return penalty
    }

    static func measureText(font: NSFont, text: String) -> CGFloat {
        guard !text.isEmpty else { return 0 }
        let s = text as NSString
        let attrs: [NSAttributedString.Key: Any] = [.font: font]
        return s.size(withAttributes: attrs).width
    }
}
