import Foundation
import Security

struct API {
    var base: URL
    var token: String?
    func request(_ path: String, method: String = "GET", body: Data? = nil) throws -> URLRequest {
        guard var components = URLComponents(url: base, resolvingAgainstBaseURL: false) else { throw APIError(message: "服务器地址无效。") }
        let parts = path.split(separator: "?", maxSplits: 1).map(String.init)
        components.path = base.path.trimmingCharacters(in: CharacterSet(charactersIn: "/")).isEmpty ? "/" + parts[0] : base.path.trimmingCharacters(in: CharacterSet(charactersIn: "/")).withLeadingSlash + "/" + parts[0]
        components.query = parts.count > 1 ? parts[1] : nil
        guard let url = components.url else { throw APIError(message: "服务器地址无效。") }
        var r = URLRequest(url: url); r.httpMethod = method; r.httpBody = body; r.timeoutInterval = 45
        r.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let token { r.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization") }
        return r
    }
    func call<T: Decodable>(_ path: String, method: String = "GET", body: [String: Any]? = nil) async throws -> T {
        let encoded = try body.map { try JSONSerialization.data(withJSONObject: $0) }
        let (data, response) = try await URLSession.shared.data(for: request(path, method: method, body: encoded))
        try Self.check(data, response)
        return try JSONDecoder().decode(T.self, from: data)
    }
    func ignore(_ path: String, method: String = "POST", body: [String: Any]? = nil) async throws { let _: JSONValue = try await call(path, method: method, body: body) }
    static func check(_ data: Data, _ response: URLResponse) throws {
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            let value = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any]
            throw APIError(message: value?["detail"] as? String ?? "请求未完成，请检查网络与服务器设置。", status:(response as? HTTPURLResponse)?.statusCode)
        }
    }
}
private extension String { var withLeadingSlash: String { "/" + self } }

struct SavedSession: Codable { var base: String; var token: String; var account: Account }
enum SecureSession {
    private static let service = "com.nightharbor.session"
    static func load() -> SavedSession? {
        let q: [String: Any] = [kSecClass as String:kSecClassGenericPassword, kSecAttrService as String:service, kSecReturnData as String:true, kSecMatchLimit as String:kSecMatchLimitOne]
        var result: CFTypeRef?; guard SecItemCopyMatching(q as CFDictionary, &result) == errSecSuccess, let data = result as? Data else { return nil }
        return try? JSONDecoder().decode(SavedSession.self, from: data)
    }
    static func save(_ value: SavedSession?) throws {
        let q: [String: Any] = [kSecClass as String:kSecClassGenericPassword, kSecAttrService as String:service]
        SecItemDelete(q as CFDictionary)
        if let value { var v = q; v[kSecValueData as String] = try JSONEncoder().encode(value); v[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly; guard SecItemAdd(v as CFDictionary, nil) == errSecSuccess else { throw APIError(message: "无法安全保存登录状态。") } }
    }
}

#if DEBUG
/// Deterministic offline acceptance: deny every URL loading request; never fake data.
final class OfflineAcceptanceProtocol: URLProtocol {
    override class func canInit(with request: URLRequest) -> Bool { ["http", "https"].contains(request.url?.scheme ?? "") }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }
    override func startLoading() { client?.urlProtocol(self,didFailWithError:URLError(.notConnectedToInternet)) }
    override func stopLoading() { }
}
#endif
