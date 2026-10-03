import SwiftUI
import UniformTypeIdentifiers

extension Color {
    static let harbor = Color(red:0.045,green:0.065,blue:0.12)
    static let panel = Color(red:0.085,green:0.11,blue:0.17)
    static let cream = Color(red:0.93,green:0.91,blue:0.84)
    static let sage = Color(red:0.64,green:0.76,blue:0.69)
    static let quiet = Color(red:0.55,green:0.61,blue:0.69)
}
struct HarborButton: ViewModifier {
    func body(content: Content) -> some View { content.font(.system(size:16,weight:.semibold)).foregroundStyle(Color.harbor).frame(maxWidth:.infinity).padding(.vertical,17).background(Color.sage,in:RoundedRectangle(cornerRadius:18)) }
}
struct SceneArt: View {
    var compact = false
    var body: some View {
        GeometryReader { g in
            ZStack {
                LinearGradient(colors:[Color(red:0.13,green:0.22,blue:0.29),Color(red:0.065,green:0.10,blue:0.17)], startPoint:.topLeading,endPoint:.bottomTrailing)
                Circle().fill(Color.cream.opacity(0.09)).frame(width:g.size.width*0.72).blur(radius:28).offset(x:70,y:-45)
                Circle().fill(Color(red:0.86,green:0.82,blue:0.64)).frame(width:34,height:34).blur(radius:0.5).offset(x:g.size.width*0.23,y:-g.size.height*0.22)
                Path { p in p.move(to:CGPoint(x:0,y:g.size.height*0.73)); p.addQuadCurve(to:CGPoint(x:g.size.width,y:g.size.height*0.7),control:CGPoint(x:g.size.width*0.4,y:g.size.height*0.35)); p.addLine(to:CGPoint(x:g.size.width,y:g.size.height)); p.addLine(to:CGPoint(x:0,y:g.size.height)) }.fill(Color(red:0.075,green:0.14,blue:0.17))
                VStack(spacing:0) {
                    UnevenRoundedRectangle(topLeadingRadius:3,topTrailingRadius:3).fill(Color(red:0.12,green:0.16,blue:0.19)).frame(width:g.size.width*0.43,height:12)
                    HStack(spacing:14) { ForEach(0..<3) { _ in RoundedRectangle(cornerRadius:3).fill(Color(red:0.75,green:0.61,blue:0.35)).overlay(Rectangle().fill(Color.harbor.opacity(0.6)).frame(width:2)).shadow(color:.yellow.opacity(0.15),radius:12) } }.padding(16).frame(width:g.size.width*0.38,height:g.size.height*0.27).background(Color(red:0.11,green:0.14,blue:0.16))
                }.offset(x:-g.size.width*0.07,y:g.size.height*0.17)
                ForEach(0..<24) { i in Capsule().fill(Color.white.opacity(0.08)).frame(width:1,height:12).rotationEffect(.degrees(15)).position(x:CGFloat((i * 73 + 13) % max(1,Int(g.size.width))),y:CGFloat((i * 41 + 11) % max(1,Int(g.size.height)))) }
            }
        }.accessibilityHidden(true)
    }
}
struct RootView: View {
    @EnvironmentObject var store: HarborStore
    @EnvironmentObject var player: SleepPlayer
    @State private var tab = 0
    @State private var showPlayer = false
    var body: some View {
        Group {
            if store.account == nil { LoginView() }
            else {
                if #available(iOS 26.1, *) {
                    tabs.tabViewBottomAccessory(isEnabled:player.current != nil) {
                        MiniPlayerView(showPlayer:$showPlayer)
                    }
                } else if #available(iOS 26.0, *) {
                    tabs.tabViewBottomAccessory {
                        if player.current != nil { MiniPlayerView(showPlayer:$showPlayer) }
                    }
                } else {
                    tabs
                }
            }
        }.preferredColorScheme(.dark).foregroundStyle(Color.cream)
        .sheet(isPresented:$showPlayer) { PlayerView() }
        .onChange(of:store.podcasts.map(\.id)) { _, ids in if let id = player.current?.id, !ids.contains(id) { player.stop() } }
        .alert("请稍等一下",isPresented:Binding(get:{store.error != nil || player.error != nil},set:{ if !$0 { store.error = nil; player.error = nil } })) { Button("知道了",role:.cancel) { store.error = nil; player.error = nil } } message: { Text(store.error ?? player.error ?? "") }
    }
    private var tabs: some View {
        TabView(selection:$tab) {
            TonightView(showPlayer:$showPlayer)
                .modifier(LegacyMiniPlayerInset(showPlayer:$showPlayer))
                .tabItem { Label("今晚",systemImage:"moon.stars") }.tag(0)
            LibraryView(showPlayer:$showPlayer)
                .modifier(LegacyMiniPlayerInset(showPlayer:$showPlayer))
                .tabItem { Label("我的播客",systemImage:"square.stack") }.tag(1)
            SettingsView()
                .modifier(LegacyMiniPlayerInset(showPlayer:$showPlayer))
                .tabItem { Label("我的",systemImage:"person.crop.circle") }.tag(2)
        }.tint(.sage)
    }
}
private struct LegacyMiniPlayerInset: ViewModifier {
    @Binding var showPlayer: Bool
    func body(content: Content) -> some View {
        if #available(iOS 26.0, *) { content }
        else {
            // Reserve space inside each tab, above the system tab bar.
            content.safeAreaInset(edge:.bottom,spacing:0) {
                MiniPlayerView(showPlayer:$showPlayer).background(Color.panel)
            }
        }
    }
}
private struct MiniPlayerView: View {
    @EnvironmentObject var player: SleepPlayer
    @Binding var showPlayer: Bool
    var body: some View {
        if let current = player.current {
            HStack(spacing:13) {
                Image(systemName:"waveform").foregroundStyle(Color.sage)
                Button { showPlayer = true } label: {
                    VStack(alignment:.leading,spacing:3) {
                        Text(current.title).font(.subheadline.weight(.medium)).lineLimit(1)
                        Text(player.playing ? "正在播放 · \(clockText(player.position))" : "已暂停").font(.caption).foregroundStyle(Color.quiet)
                    }.frame(maxWidth:.infinity,alignment:.leading)
                }.buttonStyle(.plain).accessibilityIdentifier("miniPlayerOpen")
                Button { player.playing ? player.pause() : player.resume() } label: {
                    Image(systemName:player.playing ? "pause.fill" : "play.fill").frame(width:44,height:44)
                }.accessibilityLabel(player.playing ? "暂停" : "播放").accessibilityIdentifier("miniPlayerToggle")
            }.padding(.horizontal,20).padding(.vertical,5)
        }
    }
}
struct LoginView: View {
    @EnvironmentObject var store: HarborStore
    @State private var email = ""
    @State private var password = ""
    @State private var name = ""
    @State private var invite = ""
    @State private var register = false
    @State private var showServer = false
    @State private var server = ""
    var body: some View {
        ScrollView {
            VStack(alignment:.leading,spacing:22) {
                HStack { Image(systemName:"moon.stars").foregroundStyle(Color.sage); Text("夜航").font(.title3.weight(.semibold)); Spacer(); Text("NIGHT HARBOR").font(.caption2).tracking(2).foregroundStyle(Color.quiet) }.padding(.top,22)
                SceneArt().frame(height:210).clipShape(RoundedRectangle(cornerRadius:30))
                VStack(alignment:.leading,spacing:10) { Text("为今晚，\n留一盏灯。").font(.system(size:36,weight:.light,design:.serif)); Text("你的故事，熟悉的声音。\n从一个安静的地方，慢慢进入夜晚。").font(.subheadline).foregroundStyle(Color.quiet).lineSpacing(5) }
                VStack(spacing:13) {
                    TextField("邮箱",text:$email).keyboardType(.emailAddress).textContentType(.username).textInputAutocapitalization(.never).autocorrectionDisabled().accessibilityIdentifier("email")
                    SecureField("密码 · 至少 10 位",text:$password).textContentType(register ? .newPassword : .password).accessibilityIdentifier("password")
                    if register { TextField("怎么称呼你",text:$name); SecureField("邀请码（如需要）",text:$invite) }
                }.padding(18).background(Color.panel,in:RoundedRectangle(cornerRadius:18)).textFieldStyle(.plain)
                Button { Task { await store.authenticate(email:email,password:password,name:name,invite:invite,register:register) } } label: { HStack { if store.busy { ProgressView().tint(.harbor) }; Text(register ? "创建我的夜航" : "登录，回到夜航") }.modifier(HarborButton()) }.disabled(store.busy || email.isEmpty || password.count < 10).accessibilityIdentifier("authenticate")
                HStack { Button(register ? "已有账户？登录" : "第一次来？创建账户") { register.toggle() }; Spacer(); Button("服务器") { server = store.base; showServer = true } }.font(.footnote).foregroundStyle(Color.quiet)
                Text("与 Web 工作室使用同一账户，作品和收听进度自动同步。").font(.caption).foregroundStyle(Color.quiet).lineSpacing(4)
            }.padding(26)
        }.background(Color.harbor)
        .sheet(isPresented:$showServer) { NavigationStack { Form { TextField("API 地址",text:$server).textInputAutocapitalization(.never).autocorrectionDisabled(); Text("本地调试：http://127.0.0.1:3211/podcast/api").font(.caption) }.navigationTitle("服务器设置").toolbar { ToolbarItem(placement:.confirmationAction) { Button("保存") { do { try store.setBase(server); showServer = false } catch { store.error = error.localizedDescription } } }; ToolbarItem(placement:.cancellationAction) { Button("取消") { showServer = false } } } } }
    }
}
struct TonightView: View {
    @EnvironmentObject var store: HarborStore
    @EnvironmentObject var player: SleepPlayer
    @Binding var showPlayer: Bool
    @State private var create = false
    @State private var selected: Podcast?
    var featured: Podcast? { store.podcasts.first(where:{$0.status == "ready" && !$0.completed}) ?? store.podcasts.first(where:{$0.status == "ready"}) }
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment:.leading,spacing:26) {
                    HStack { VStack(alignment:.leading,spacing:6) { Text("NIGHT HARBOR").font(.caption2).tracking(3).foregroundStyle(Color.sage); Text("今晚，慢下来。").font(.system(size:30,weight:.light,design:.serif)) }; Spacer(); Image(systemName:"moon.stars").font(.title2).foregroundStyle(Color.sage) }.padding(.top,10)
                    if let note = store.connectionNote { Label(note,systemImage:"wifi.slash").font(.caption).foregroundStyle(Color.quiet) }
                    VStack(alignment:.leading,spacing:0) {
                        SceneArt().frame(height:240)
                        VStack(alignment:.leading,spacing:14) {
                            Text(featured == nil ? "你的第一处夜晚" : "为你留好的声音").font(.caption).foregroundStyle(Color.sage)
                            Text(featured?.title ?? "从雨夜旅馆开始").font(.title2.weight(.medium))
                            Text(featured.map { "\(clockText($0.duration_seconds ?? 0)) · \($0.voice) · \(store.cachedURL($0.id) == nil ? "可下载收听" : "已下载，可离线收听")" } ?? "准备一段属于自己的故事，\n让熟悉的声音陪你度过安静的夜晚。").font(.subheadline).foregroundStyle(Color.quiet).lineSpacing(4)
                            Button { if let p = featured { Task { await player.play(p,store:store); if player.current != nil { showPlayer = true } } } else { create = true } } label: { HStack { if player.loading { ProgressView().tint(.harbor) }; Image(systemName:featured == nil ? "plus" : "play.fill"); Text(player.loading ? "正在下载，准备播放…" : featured == nil ? "制作第一段播客" : "开始今晚") }.modifier(HarborButton()) }.disabled(player.loading)
                        }.padding(22)
                    }.background(Color.panel,in:RoundedRectangle(cornerRadius:28)).clipShape(RoundedRectangle(cornerRadius:28))
                    let active = store.podcasts.filter { $0.isActive || $0.status == "failed" }
                    if !active.isEmpty { VStack(alignment:.leading,spacing:14) { Text("正在准备的夜晚").font(.headline); ForEach(active) { p in Button { selected = p } label: { PodcastRow(podcast:p) }.buttonStyle(.plain) } } }
                    HStack(alignment:.top,spacing:12) { Image(systemName:"sparkle").foregroundStyle(Color.sage); Text("不必听完，也不必记住。\n你可以随时让故事慢慢远去。").font(.subheadline).foregroundStyle(Color.quiet).lineSpacing(5) }.padding(.horizontal,8)
                }.padding(24)
            }.background(Color.harbor).refreshable { await store.refresh() }.toolbar(.hidden,for:.navigationBar)
            .sheet(isPresented:$create) { EditorView() }
            .sheet(item:$selected) { p in DetailView(id:p.id,showPlayer:$showPlayer) }
        }
    }
}
struct PodcastRow: View {
    @EnvironmentObject var store: HarborStore
    let podcast: Podcast
    var body: some View {
        HStack(spacing:14) {
            ZStack { RoundedRectangle(cornerRadius:16).fill(Color.sage.opacity(0.1)); Image(systemName:podcast.status == "ready" ? "moon.zzz" : podcast.status == "failed" ? "exclamationmark.circle" : "waveform").font(.title3).foregroundStyle(Color.sage) }.frame(width:56,height:62)
            VStack(alignment:.leading,spacing:7) { Text(podcast.title).font(.subheadline.weight(.medium)).lineLimit(2); HStack { Text(podcast.statusLabel); if podcast.status == "ready" { Text("· \(clockText(podcast.duration_seconds ?? 0))"); if store.cachedURL(podcast.id) != nil { Image(systemName:"arrow.down.circle.fill") } } }.font(.caption).foregroundStyle(Color.quiet); if podcast.isActive { ProgressView(value:Double(podcast.progress),total:100).tint(.sage); Text(podcast.stage).font(.caption2).foregroundStyle(Color.quiet) } }
            Spacer(minLength:0); Image(systemName:"chevron.right").font(.caption).foregroundStyle(Color.quiet)
        }.padding(14).background(Color.panel,in:RoundedRectangle(cornerRadius:20))
    }
}
struct LibraryView: View {
    @EnvironmentObject var store: HarborStore
    @Binding var showPlayer: Bool
    @State private var create = false
    @State private var selected: Podcast?
    @State private var filter = 0
    var filtered: [Podcast] { store.podcasts.filter { filter == 0 || (filter == 1 && $0.status == "ready") || (filter == 2 && store.cachedURL($0.id) != nil) } }
    var body: some View {
        NavigationStack {
            ScrollView { VStack(alignment:.leading,spacing:20) {
                Picker("显示",selection:$filter) { Text("全部").tag(0); Text("可收听").tag(1); Text("已下载").tag(2) }.pickerStyle(.segmented)
                if filtered.isEmpty { VStack(spacing:18) { Image(systemName:"books.vertical").font(.system(size:38,weight:.ultraLight)).foregroundStyle(Color.sage); Text(filter == 2 ? "把声音留在身边" : "这里会收藏你的夜晚").font(.title3); Text(filter == 2 ? "下载后的播客可以在没有网络时收听。" : "在这里制作，或在 Web 工作室提交脚本。\n从草稿到可以收听，进度都会在这里更新。").font(.subheadline).foregroundStyle(Color.quiet).multilineTextAlignment(.center).lineSpacing(5); Button("制作播客") { create = true }.modifier(HarborButton()) }.padding(.vertical,70) }
                ForEach(filtered) { p in Button { selected = p } label: { PodcastRow(podcast:p) }.buttonStyle(.plain) }
            }.padding(24) }.background(Color.harbor).navigationTitle("我的播客").toolbar { Button { create = true } label: { Image(systemName:"plus") }.accessibilityLabel("制作播客") }.refreshable { await store.refresh() }
            .sheet(isPresented:$create) { EditorView() }.sheet(item:$selected) { p in DetailView(id:p.id,showPlayer:$showPlayer) }
        }
    }
}
struct DetailView: View {
    @EnvironmentObject var store: HarborStore
    @EnvironmentObject var player: SleepPlayer
    @Environment(\.dismiss) var dismiss
    var id: String
    @Binding var showPlayer: Bool
    @State private var edit = false
    @State private var deleting = false
    @State private var generating = false
    @State private var working = false
    @State private var events: [LifecycleEvent] = []
    var podcast: Podcast? { store.podcasts.first { $0.id == id } }
    var body: some View {
        NavigationStack {
            ScrollView {
                if let p = podcast {
                    VStack(alignment:.leading,spacing:22) {
                        SceneArt().frame(height:200).clipShape(RoundedRectangle(cornerRadius:24))
                        Text(p.title).font(.title2.weight(.medium)); Label(p.statusLabel,systemImage:p.status == "ready" ? "checkmark.circle" : "waveform").foregroundStyle(Color.sage)
                        if p.isActive { ProgressView(value:Double(p.progress),total:100).tint(.sage); Text("\(p.stage) · \(p.progress)%").font(.subheadline).foregroundStyle(Color.quiet) }
                        if let error = p.error, !error.isEmpty { Text(error).font(.subheadline).foregroundStyle(Color.orange).textSelection(.enabled) }
                        if p.status == "ready" {
                            Text("\(clockText(p.duration_seconds ?? 0)) · \(p.voice)").foregroundStyle(Color.quiet)
                            Button { working = true; Task { await player.play(p,store:store); working = false; if player.current != nil { dismiss(); DispatchQueue.main.asyncAfter(deadline:.now()+0.4) { showPlayer = true } } } } label: { Label(working ? "下载并准备播放…" : "继续收听",systemImage:"play.fill").modifier(HarborButton()) }.disabled(working || store.downloads.contains(p.id))
                            if store.cachedURL(p.id) != nil { Label("已下载 · 可离线收听",systemImage:"arrow.down.circle.fill").font(.subheadline).foregroundStyle(Color.sage); Button("移除本机下载",role:.destructive) { if player.current?.id == p.id { player.stop() }; store.removeDownload(p.id) } }
                            else { Button { Task { do { _ = try await store.audio(for:p) } catch { store.error = error.localizedDescription } } } label: { Label(store.downloads.contains(p.id) ? "正在下载…" : "下载到本机",systemImage:"arrow.down.circle") }.disabled(store.downloads.contains(p.id)) }
                        }
                        if p.canEdit { Button { edit = true } label: { Label("编辑脚本与听感",systemImage:"slider.horizontal.3") }; Button { generating = true } label: { Label(p.status == "draft" ? "生成播客" : "重新生成",systemImage:"sparkles").modifier(HarborButton()) } }
                        if p.isActive { Button("取消制作",role:.destructive) { Task { await store.action("cancel",podcast:p) } } }
                        VStack(alignment:.leading,spacing:14) { Text("制作记录").font(.headline); if events.isEmpty { Text("暂无记录").foregroundStyle(Color.quiet) }; ForEach(events) { e in HStack(alignment:.top,spacing:12) { Circle().fill(Color.sage.opacity(0.6)).frame(width:6,height:6).padding(.top,6); VStack(alignment:.leading,spacing:4) { Text(e.stage).font(.subheadline); Text(e.created_at.replacingOccurrences(of:"T",with:" ").prefix(19)).font(.caption).foregroundStyle(Color.quiet) } } } }.padding(20).frame(maxWidth:.infinity,alignment:.leading).background(Color.panel,in:RoundedRectangle(cornerRadius:20))
                        Button("删除播客",role:.destructive) { deleting = true }.padding(.top,8)
                    }.padding(24)
                } else { ContentUnavailableView("作品已移除",systemImage:"moon") }
            }.background(Color.harbor).navigationTitle("这一段夜晚").navigationBarTitleDisplayMode(.inline).toolbar { ToolbarItem(placement:.confirmationAction) { Button("完成") { dismiss() } } }
            .sheet(isPresented:$edit) { if let p = podcast { EditorView(existing:p) } }
            .confirmationDialog("删除后将从云端作品库和本机下载中移除。",isPresented:$deleting,titleVisibility:.visible) { Button("删除播客",role:.destructive) { guard let p = podcast else {return}; if player.current?.id == p.id { player.stop() }; Task { await store.action("delete",podcast:p); if store.podcasts.allSatisfy({$0.id != id}) { dismiss() } } } }
            .confirmationDialog("现在生成这份脚本？云端将调用语音服务，产生 API 用量。",isPresented:$generating,titleVisibility:.visible) { Button("开始生成") { if let p = podcast { Task { await store.action(p.status == "draft" ? "generate" : "retry",podcast:p) } } } }
            .task(id:podcast?.updated_at) { if let result: EventList = try? await store.api.call("podcasts/\(id)/events") { events = result.items } }
        }.tint(.sage)
    }
}
struct EditorView: View {
    @EnvironmentObject var store: HarborStore
    @Environment(\.dismiss) var dismiss
    var existing: Podcast? = nil
    @State private var text = ""
    @State private var title = "雨夜旅馆 · 靠窗的房间"
    @State private var voice = "Serena"
    @State private var scene = "rainy-inn"
    @State private var ambience: Double = -38
    @State private var importing = false
    @State private var saving = false
    @State private var advanced = false
    var body: some View {
        NavigationStack {
            Form {
                Section { Text("从一份完整的雨夜旅馆脚本开始，也可以导入 AI 工具为你写好的 JSON 脚本。").font(.subheadline).foregroundStyle(Color.quiet) }
                Section("这个夜晚") {
                    TextField("播客标题",text:$title)
                    Picker("场景",selection:$scene) { if let scenes = store.catalog?.scenes { ForEach(scenes) { Text($0.name).tag($0.id) } } else { Text("雨夜旅馆").tag("rainy-inn") } }
                    Picker("声音",selection:$voice) { if let voices = store.catalog?.voices { ForEach(voices) { Text($0.name).tag($0.id) } } else { Text("Serena · 温柔女声").tag("Serena") } }
                    VStack(alignment:.leading,spacing:8) { HStack { Text("环境声"); Spacer(); Text("\(Int(ambience)) dBFS").foregroundStyle(Color.quiet) }; Slider(value:$ambience,in:-60 ... -25,step:1); HStack { Text("更轻"); Spacer(); Text("更明显") }.font(.caption).foregroundStyle(Color.quiet) }
                }
                Section("脚本") {
                    Button { importing = true } label: { Label("导入 JSON 脚本",systemImage:"square.and.arrow.down") }
                    DisclosureGroup("查看与编辑完整脚本",isExpanded:$advanced) { Text("这里是完整制作脚本，包括正文、停顿和环境声安排。上方的标题、声音与环境声设置会在保存时更新到脚本中。").font(.caption).foregroundStyle(Color.quiet); TextEditor(text:$text).font(.system(size:12,design:.monospaced)).frame(minHeight:320).autocorrectionDisabled().textInputAutocapitalization(.never).accessibilityIdentifier("scriptEditor") }
                    if !advanced { Text(scriptSummary).font(.subheadline).foregroundStyle(Color.quiet).lineLimit(5) }
                }
                Section { Text("保存草稿不会调用语音生成。你可以在作品详情确认后开始制作，进度会自动同步。").font(.footnote).foregroundStyle(Color.quiet) }
            }.scrollContentBackground(.hidden).background(Color.harbor).navigationTitle(existing == nil ? "制作一段夜晚" : "编辑草稿").navigationBarTitleDisplayMode(.inline).toolbar { ToolbarItem(placement:.cancellationAction) { Button("取消") { dismiss() } }; ToolbarItem(placement:.confirmationAction) { Button(saving ? "保存中…" : "保存草稿") { save() }.disabled(saving || title.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty).accessibilityIdentifier("saveDraft") } }
            .task { if text.isEmpty { text = existing?.scriptText ?? (try? String(contentsOf:Bundle.main.url(forResource:"sample-script",withExtension:"json")!,encoding:.utf8)) ?? "{}"; scene = existing?.scene ?? store.preferences.scene; hydrate(); if existing == nil { voice = store.preferences.voice; ambience = store.preferences.ambience_dbfs } } }
            .fileImporter(isPresented:$importing,allowedContentTypes:[.json]) { result in do { let url = try result.get(); let granted = url.startAccessingSecurityScopedResource(); defer { if granted { url.stopAccessingSecurityScopedResource() } }; let data = try Data(contentsOf:url); guard data.count <= 131_072, let imported = String(data:data,encoding:.utf8) else { throw APIError(message:"请选择不大于 128 KiB 的 UTF-8 JSON 文件。") }; _ = try parseScript(imported); text = imported; hydrate() } catch { store.error = error.localizedDescription } }
        }.tint(.sage)
    }
    func save() {
        UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder),to:nil,from:nil,for:nil)
        saving = true
        Task { do { let value = try preparedScript(); if await store.saveDraft(text:value,scene:scene,existing:existing) != nil { dismiss() } } catch { store.error = error.localizedDescription }; saving = false }
    }
    var scriptSummary: String { guard let data = text.data(using:.utf8), let obj = try? JSONSerialization.jsonObject(with:data) as? [String:Any], let segments = obj["segments"] as? [[String:Any]] else { return "请导入或填写完整脚本。" }; return "\(segments.count) 个分段\n" + (segments.first?["text"] as? String ?? "") }
    func hydrate() { guard let data = text.data(using:.utf8), let obj = try? JSONSerialization.jsonObject(with:data) as? [String:Any] else {return}; title = obj["title"] as? String ?? title; voice = obj["voice"] as? String ?? voice; ambience = (obj["mix"] as? [String:Any])?["ambience_dbfs"] as? Double ?? ambience }
    func preparedScript() throws -> String { _ = try parseScript(text); var obj = try JSONSerialization.jsonObject(with:Data(text.utf8)) as! [String:Any]; obj["title"] = title; obj["voice"] = voice; if existing == nil { obj["id"] = UUID().uuidString }; var mix = obj["mix"] as? [String:Any] ?? [:]; mix["ambience_dbfs"] = ambience; obj["mix"] = mix; return String(data:try JSONSerialization.data(withJSONObject:obj,options:[.prettyPrinted,.sortedKeys]),encoding:.utf8)! }
}
struct PlayerView: View {
    @EnvironmentObject var player: SleepPlayer
    @Environment(\.dismiss) var dismiss
    @State private var seeking: Double = 0
    @State private var scrubbing = false
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing:26) {
                    Text("让夜晚慢慢靠岸").font(.caption).tracking(3).foregroundStyle(Color.quiet).padding(.top,12)
                    SceneArt().frame(height:285).clipShape(RoundedRectangle(cornerRadius:35)).padding(.horizontal,6)
                    VStack(spacing:9) { Text(player.current?.title ?? "夜航").font(.title2.weight(.medium)).multilineTextAlignment(.center); Text("熟悉的声音 · 安静的陪伴").font(.subheadline).foregroundStyle(Color.quiet) }
                    VStack(spacing:6) { Slider(value:Binding(get:{scrubbing ? seeking : min(player.position,max(1,player.duration))},set:{seeking = $0}),in:0 ... max(1,player.duration),onEditingChanged:{ editing in if editing { seeking = player.position; scrubbing = true } else { scrubbing = false; player.seek(seeking) } }).tint(.sage).accessibilityLabel("播放进度"); HStack { Text(clockText(scrubbing ? seeking : player.position)).accessibilityIdentifier("playbackElapsed"); Spacer(); Text(clockText(player.duration)) }.font(.caption.monospacedDigit()).foregroundStyle(Color.quiet) }
                    HStack(spacing:48) {
                        Button { player.seek(player.position - 15) } label: { Image(systemName:"gobackward.15").font(.system(size:29,weight:.light)) }.accessibilityLabel("后退 15 秒")
                        Button { player.playing ? player.pause() : player.resume() } label: { Image(systemName:player.playing ? "pause.fill" : "play.fill").font(.system(size:27)).foregroundStyle(Color.harbor).frame(width:78,height:78).background(Color.sage,in:Circle()) }.accessibilityLabel(player.playing ? "暂停" : "播放").accessibilityIdentifier("playerToggle")
                        Button { player.seek(player.position + 15) } label: { Image(systemName:"goforward.15").font(.system(size:29,weight:.light)) }.accessibilityLabel("前进 15 秒")
                    }
                    Menu { ForEach([0,15,30,45,60,-1],id:\.self) { value in Button(value == 0 ? "关闭定时" : value == -1 ? "本集结束" : "\(value) 分钟") { player.setTimer(value) } } } label: { Label("睡眠定时 · \(player.timerLabel)",systemImage:"moon.zzz").font(.subheadline).padding(.horizontal,22).padding(.vertical,13).background(Color.panel,in:Capsule()) }.accessibilityIdentifier("sleepTimer")
                    if let error = player.error { Text(error).font(.footnote).foregroundStyle(Color.orange).multilineTextAlignment(.center) }
                    Text("关掉屏幕，声音会继续陪着你。").font(.caption).foregroundStyle(Color.quiet)
                }.padding(26)
            }.background(Color.harbor).toolbar { ToolbarItem(placement:.topBarLeading) { Button { dismiss() } label: { Image(systemName:"chevron.down") }.accessibilityLabel("收起播放器") } }
        }.tint(.cream)
    }
}
struct SettingsView: View {
    @EnvironmentObject var store: HarborStore
    @EnvironmentObject var player: SleepPlayer
    @State private var logout = false
    @State private var prefs = Preferences()
    @State private var saved = false
    var body: some View {
        NavigationStack {
            Form {
                Section { VStack(alignment:.leading,spacing:8) { Text(store.account?.display_name.isEmpty == false ? store.account!.display_name : "夜航旅人").font(.title2); Text(store.account?.email ?? "").font(.subheadline).foregroundStyle(Color.quiet) }.padding(.vertical,12) }
                Section("默认听感") {
                    Picker("声音",selection:$prefs.voice) { if let voices = store.catalog?.voices { ForEach(voices) { Text($0.name).tag($0.id) } } else { Text("Serena").tag("Serena") } }
                    Picker("场景",selection:$prefs.scene) { if let scenes = store.catalog?.scenes { ForEach(scenes) { Text($0.name).tag($0.id) } } else { Text("雨夜旅馆").tag("rainy-inn") } }
                    VStack(alignment:.leading) { Text("环境声 · \(Int(prefs.ambience_dbfs)) dBFS"); Slider(value:$prefs.ambience_dbfs,in:-60 ... -25,step:1) }
                    Picker("睡眠定时",selection:$prefs.sleep_timer_minutes) { ForEach([0,15,30,45,60,-1],id:\.self) { v in Text(v == 0 ? "关闭" : v == -1 ? "本集结束" : "\(v) 分钟").tag(v) } }
                    Button(saved ? "已保存" : "保存默认听感") { store.preferences = prefs; Task { await store.savePreferences(); saved = store.error == nil } }
                }
                Section("我的账户") { Text("Web 工作室、App 与 MCP 使用同一作品库。登录信息安全保存在本机钥匙串。").font(.caption).foregroundStyle(Color.quiet); LabeledContent("服务器",value:URL(string:store.base)?.host ?? "").font(.footnote); if let url = URL(string:store.base)?.deletingLastPathComponent() { Link("打开 Web 工作室",destination:url) }; Button("退出登录",role:.destructive) { logout = true } }
                Section { Text("夜航 · Night Harbor\n给每个夜晚，一处可以停靠的地方。").font(.caption).foregroundStyle(Color.quiet).frame(maxWidth:.infinity).multilineTextAlignment(.center).padding(.vertical,12) }
            }.scrollContentBackground(.hidden).background(Color.harbor).navigationTitle("我的").confirmationDialog("退出后，本机下载将保留；重新登录同一账户可继续收听。",isPresented:$logout,titleVisibility:.visible) { Button("退出登录",role:.destructive) { player.stop(); Task { await store.logout() } } }
        }.tint(.sage).onAppear { prefs = store.preferences }.onChange(of:prefs.voice) { _, _ in saved = false }.onChange(of:prefs.scene) { _, _ in saved = false }.onChange(of:prefs.ambience_dbfs) { _, _ in saved = false }.onChange(of:prefs.sleep_timer_minutes) { _, _ in saved = false }
    }
}
