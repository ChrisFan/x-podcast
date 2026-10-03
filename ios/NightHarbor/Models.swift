import Foundation

enum JSONValue: Codable, Equatable {
    case string(String), number(Double), bool(Bool), object([String: JSONValue]), array([JSONValue]), null
    init(from decoder: Decoder) throws {
        let c = try decoder.singleValueContainer()
        if c.decodeNil() { self = .null }
        else if let v = try? c.decode(Bool.self) { self = .bool(v) }
        else if let v = try? c.decode(Double.self) { self = .number(v) }
        else if let v = try? c.decode(String.self) { self = .string(v) }
        else if let v = try? c.decode([String: JSONValue].self) { self = .object(v) }
        else { self = .array(try c.decode([JSONValue].self)) }
    }
    func encode(to encoder: Encoder) throws {
        var c = encoder.singleValueContainer()
        switch self { case .string(let v): try c.encode(v); case .number(let v): try c.encode(v); case .bool(let v): try c.encode(v); case .object(let v): try c.encode(v); case .array(let v): try c.encode(v); case .null: try c.encodeNil() }
    }
}
struct Podcast: Codable, Identifiable {
    let id: String
    var title: String
    var scene: String
    var voice: String
    var status: String
    var progress: Int
    var stage: String
    var error: String?
    var duration_seconds: Double?
    var created_at: String
    var updated_at: String
    var script: JSONValue
    var playback_position_seconds: Double
    var completed: Bool
    var audio_url: String?
    var download_url: String?
    var isActive: Bool { ["queued", "generating", "mixing"].contains(status) }
    var canEdit: Bool { ["draft", "failed", "cancelled"].contains(status) }
    var statusLabel: String { ["draft":"草稿", "queued":"等待制作", "generating":"生成声音", "mixing":"混合环境声", "ready":"可以收听", "failed":"制作未完成", "cancelled":"已取消"][status] ?? status }
    var scriptText: String { let e = JSONEncoder(); e.outputFormatting = [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes]; return (try? String(data: e.encode(script), encoding: .utf8)) ?? "{}" }
}
struct Account: Codable { var id: String; var email: String; var display_name: String }
struct AuthResult: Codable { var token: String; var user: Account }
struct PodcastList: Codable { var items: [Podcast] }
struct CatalogOption: Codable, Identifiable { var id: String; var name: String; var description: String }
struct Catalog: Codable { var voices: [CatalogOption]; var scenes: [CatalogOption]; var script_schema: JSONValue; var defaults: JSONValue }
struct Preferences: Codable { var voice = "Serena"; var scene = "rainy-inn"; var ambience_dbfs: Double = -38; var sleep_timer_minutes = 30 }
struct LifecycleEvent: Codable, Identifiable { var status: String; var stage: String; var created_at: String; var id: String { created_at + status } }
struct EventList: Codable { var items: [LifecycleEvent] }
struct PlaybackUpdate: Codable, Equatable { var position: Double; var completed: Bool }
struct APIError: LocalizedError { var message: String; var status: Int? = nil; var errorDescription: String? { message } }

func parseScript(_ text: String) throws -> JSONValue {
    guard let data = text.data(using: .utf8), let object = try JSONSerialization.jsonObject(with: data) as? [String: Any] else { throw APIError(message: "脚本必须是一个 JSON 对象。") }
    guard (object["version"] as? Int) == 1, let title = object["title"] as? String, !title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty, let segments = object["segments"] as? [[String: Any]], !segments.isEmpty, segments.allSatisfy({ !($0["text"] as? String ?? "").trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }) else { throw APIError(message: "请使用 version 1 脚本，包含标题和至少一个有正文的 segments 分段。") }
    return try JSONDecoder().decode(JSONValue.self, from: data)
}
func clockText(_ seconds: Double) -> String { let s = max(0, Int(seconds.isFinite ? seconds : 0)); return String(format: "%d:%02d", s / 60, s % 60) }

/// AVFoundation requires a recognizable file extension for downloaded media.
func audioFileExtension(for url: URL) throws -> String {
    let file = try FileHandle(forReadingFrom:url); defer { try? file.close() }
    let bytes = [UInt8](try file.read(upToCount:12) ?? Data())
    if bytes.count >= 12, String(bytes:bytes[0..<4],encoding:.ascii) == "RIFF", String(bytes:bytes[8..<12],encoding:.ascii) == "WAVE" { return "wav" }
    if bytes.count >= 3, String(bytes:bytes[0..<3],encoding:.ascii) == "ID3" { return "mp3" }
    if bytes.count >= 2, bytes[0] == 0xff, bytes[1] & 0xe0 == 0xe0 { return "mp3" }
    throw APIError(message:"服务器返回的音频格式无法识别，请重新生成或稍后重试。")
}
