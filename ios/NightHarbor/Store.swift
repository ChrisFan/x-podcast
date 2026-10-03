import Foundation
import CryptoKit
import SwiftUI

@MainActor final class HarborStore: ObservableObject {
    @Published var account: Account?
    @Published var podcasts: [Podcast] = []
    @Published var catalog: Catalog?
    @Published var preferences = Preferences()
    @Published var error: String?
    @Published var connectionNote: String?
    @Published var busy = false
    @Published var downloads: Set<String> = []
    @Published var cacheRevision = 0
    @Published var base: String
    private var token: String?
    private var poll: Task<Void, Never>?
    private var pending: [String: PlaybackUpdate] = [:]
    private var identity: String { base + "|" + (account?.id ?? "guest") }
    var api: API { API(base: URL(string: base)!, token: token) }
    var cacheDirectory: URL {
        let digest = SHA256.hash(data: Data(identity.utf8)).map { String(format:"%02x", $0) }.joined()
        return FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask)[0].appendingPathComponent("NightHarbor/\(digest)")
    }
    var metadataURL: URL { cacheDirectory.appendingPathComponent("library.json") }
    init() {
        #if DEBUG
        let arguments = ProcessInfo.processInfo.arguments
        if arguments.contains("--uitest-offline") { URLProtocol.registerClass(OfflineAcceptanceProtocol.self) }
        if arguments.contains("--uitest-reset") { try? SecureSession.save(nil) }
        if let index = arguments.firstIndex(of:"--api-base"), arguments.indices.contains(index + 1) { UserDefaults.standard.set(arguments[index + 1],forKey:"apiBase") }
        #endif
        let saved = SecureSession.load()
        base = saved?.base ?? UserDefaults.standard.string(forKey:"apiBase") ?? "https://alu-designer.pawlpixel.com/podcast/api"
        token = saved?.token; account = saved?.account
        if account != nil { restoreMetadata(); startPolling() }
    }
    func setBase(_ value: String) throws {
        let normalized = value.trimmingCharacters(in: .whitespacesAndNewlines).trimmingCharacters(in: CharacterSet(charactersIn:"/"))
        guard let url = URL(string: normalized), let host = url.host, url.user == nil, url.password == nil, url.query == nil, url.fragment == nil,
              url.scheme == "https" || (url.scheme == "http" && ["localhost", "127.0.0.1", "::1"].contains(host)) else { throw APIError(message:"请填写 HTTPS API 地址；本地调试可用 http://127.0.0.1:3211/podcast/api。") }
        base = normalized; UserDefaults.standard.set(base, forKey:"apiBase")
    }
    func authenticate(email: String, password: String, name: String, invite: String, register: Bool) async {
        busy = true; defer { busy = false }
        do {
            var body = ["email":email.trimmingCharacters(in:.whitespacesAndNewlines), "password":password]
            if register { body["display_name"] = name.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty ? "夜航旅人" : name; if !invite.isEmpty { body["invite_code"] = invite } }
            let result: AuthResult = try await api.call(register ? "auth/register" : "auth/login", method:"POST", body:body)
            try SecureSession.save(SavedSession(base:base, token:result.token, account:result.user))
            token = result.token; account = result.user; restoreMetadata(); await refresh(); startPolling()
        } catch { self.error = error.localizedDescription }
    }
    func logout() async {
        poll?.cancel(); try? await api.ignore("auth/logout"); try? SecureSession.save(nil)
        account = nil; token = nil; podcasts = []; catalog = nil; pending = [:]; connectionNote = nil
    }
    func stopPolling() { poll?.cancel(); poll = nil }
    func startPolling() {
        guard account != nil else { return }
        poll?.cancel(); poll = Task { [weak self] in
            while !Task.isCancelled { await self?.refresh(); try? await Task.sleep(nanoseconds: 5_000_000_000) }
        }
    }
    func refresh() async {
        guard account != nil else { return }
        let scope = identity
        do {
            for (id, position) in pending {
                do { try await api.ignore("podcasts/\(id)/progress", body:["position_seconds":position.position, "completed":position.completed]); if pending[id] == position { pending.removeValue(forKey:id) } }
                catch let error as APIError where error.status == 404 || error.status == 409 { pending.removeValue(forKey:id) }
            }
            let list: PodcastList = try await api.call("podcasts")
            guard scope == identity else { return }
            for removed in podcasts where !list.items.contains(where:{$0.id == removed.id}) { removeDownload(removed.id) }; podcasts = list.items; connectionNote = nil; saveMetadata()
            if catalog == nil { catalog = try? await api.call("catalog") }; if let p: Preferences = try? await api.call("preferences"), scope == identity { preferences = p }
        } catch { if scope == identity { connectionNote = (error as? APIError)?.status == 401 ? "登录已过期 · 可离线收听，请在「我的」重新登录" : "暂时无法连接 · 已下载的内容仍可收听" } }
    }
    func restoreMetadata() {
        if let data = try? Data(contentsOf: metadataURL), let list = try? JSONDecoder().decode([Podcast].self, from:data) { podcasts = list }
        else { podcasts = [] }
        if let data = try? Data(contentsOf: cacheDirectory.appendingPathComponent("pending.json")), let value = try? JSONDecoder().decode([String:PlaybackUpdate].self, from:data) { pending = value }
    }
    func saveMetadata() {
        try? FileManager.default.createDirectory(at:cacheDirectory, withIntermediateDirectories:true)
        if let data = try? JSONEncoder().encode(podcasts) { try? data.write(to:metadataURL, options:.atomic) }
        if let data = try? JSONEncoder().encode(pending) { try? data.write(to:cacheDirectory.appendingPathComponent("pending.json"), options:.atomic) }
    }
    func cachedURL(_ id: String) -> URL? {
        for ext in ["mp3", "wav"] {
            let path = cacheDirectory.appendingPathComponent("\(id).\(ext)")
            if FileManager.default.fileExists(atPath:path.path) { return path }
        }
        let legacy = cacheDirectory.appendingPathComponent("\(id).audio")
        if FileManager.default.fileExists(atPath:legacy.path), let ext = try? audioFileExtension(for:legacy) {
            let target = cacheDirectory.appendingPathComponent("\(id).\(ext)")
            do { try FileManager.default.moveItem(at:legacy,to:target); return target } catch { return nil }
        }
        return nil
    }
    func audio(for podcast: Podcast) async throws -> URL {
        if let url = cachedURL(podcast.id) { return url }
        guard !downloads.contains(podcast.id) else { throw APIError(message:"音频正在下载，请稍候。") }
        let scope = identity; let directory = cacheDirectory
        downloads.insert(podcast.id); defer { downloads.remove(podcast.id) }
        let (temporary, response) = try await URLSession.shared.download(for: api.request("podcasts/\(podcast.id)/audio?variant=mix"))
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else { throw APIError(message:"音频下载未完成，请稍后重试。") }
        guard scope == identity, podcasts.contains(where:{$0.id == podcast.id && $0.status == "ready"}) else { throw APIError(message:"账户或作品状态已改变，下载已停止。") }
        try FileManager.default.createDirectory(at:directory, withIntermediateDirectories:true)
        let ext = try audioFileExtension(for:temporary)
        let target = directory.appendingPathComponent("\(podcast.id).\(ext)")
        try FileManager.default.moveItem(at:temporary, to:target); cacheRevision += 1
        return target
    }
    func removeDownload(_ id: String) { if let path = cachedURL(id) { try? FileManager.default.removeItem(at:path); cacheRevision += 1 } }
    func saveDraft(text: String, scene: String, existing: Podcast?) async -> Podcast? {
        do {
            let script = try parseScript(text)
            let data = try JSONEncoder().encode(script)
            let object = try JSONSerialization.jsonObject(with:data)
            let result: Podcast = try await api.call(existing.map { "podcasts/\($0.id)" } ?? "podcasts", method:existing == nil ? "POST" : "PATCH", body:["script":object, "scene":scene])
            await refresh(); return result
        } catch { self.error = error.localizedDescription; return nil }
    }
    func action(_ action: String, podcast: Podcast) async {
        do {
            if action == "delete" { try await api.ignore("podcasts/\(podcast.id)", method:"DELETE"); removeDownload(podcast.id); pending.removeValue(forKey:podcast.id) }
            else { let _: Podcast = try await api.call("podcasts/\(podcast.id)/\(action)", method:"POST", body:action == "cancel" ? [:] : ["request_id":UUID().uuidString]) }
            await refresh()
        } catch { self.error = error.localizedDescription }
    }
    func progress(id: String, position: Double, completed: Bool = false) async {
        guard account != nil, position.isFinite else { return }
        let update = PlaybackUpdate(position:position, completed:completed)
        let scope = identity
        pending[id] = update; if let index = podcasts.firstIndex(where:{$0.id == id}) { podcasts[index].playback_position_seconds = position; podcasts[index].completed = completed }; saveMetadata()
        do { try await api.ignore("podcasts/\(id)/progress", body:["position_seconds":position, "completed":completed]); if scope == identity, pending[id] == update { pending.removeValue(forKey:id); saveMetadata() } } catch { }
    }
    func savePreferences() async {
        do { let data = try JSONEncoder().encode(preferences); let body = try JSONSerialization.jsonObject(with:data) as! [String:Any]; let p: Preferences = try await api.call("preferences", method:"PUT", body:body); preferences = p } catch { self.error = error.localizedDescription }
    }
}
