import Foundation
import AVFoundation
import MediaPlayer

@MainActor final class SleepPlayer: ObservableObject {
    @Published var current: Podcast?
    @Published var playing = false
    @Published var loading = false
    @Published var position: Double = 0
    @Published var duration: Double = 0
    @Published var timerMinutes = 0
    @Published var remaining: Int = 0
    @Published var error: String?
    private var player = AVPlayer()
    private var observer: Any?
    private var endObserver: NSObjectProtocol?
    private var interruptionObserver: NSObjectProtocol?
    private var routeObserver: NSObjectProtocol?
    private var itemObserver: NSKeyValueObservation?
    private var timer: Timer?
    private var deadline: Date?
    private var store: HarborStore?
    private var lastSync: Double = -1
    private var endOfTrack = false
    init() {
        observer = player.addPeriodicTimeObserver(forInterval:CMTime(seconds:1, preferredTimescale:600), queue:.main) { [weak self] time in
            Task { @MainActor in
                guard let self else { return }; self.position = time.seconds.isFinite ? time.seconds : 0
                let value = self.player.currentItem?.duration.seconds ?? 0
                if value.isFinite && value > 0 { self.duration = value }
                self.playing = self.player.timeControlStatus == .playing
                self.updateNowPlaying()
                if self.playing && abs(self.position - self.lastSync) > 10 { self.lastSync = self.position; await self.sync() }
            }
        }
        endObserver = NotificationCenter.default.addObserver(forName:.AVPlayerItemDidPlayToEndTime, object:nil, queue:.main) { [weak self] note in
            Task { @MainActor in guard let self, let item = note.object as? AVPlayerItem, item === self.player.currentItem else { return }; self.playing = false; self.position = self.duration; self.setTimer(0); await self.sync(completed:true) }
        }
        interruptionObserver = NotificationCenter.default.addObserver(forName:AVAudioSession.interruptionNotification, object:nil, queue:.main) { [weak self] note in
            let kind = note.userInfo?[AVAudioSessionInterruptionTypeKey] as? UInt
            if kind == AVAudioSession.InterruptionType.began.rawValue { Task { @MainActor in self?.pause() } }
        }
        routeObserver = NotificationCenter.default.addObserver(forName:AVAudioSession.routeChangeNotification, object:nil, queue:.main) { [weak self] note in
            let reason = note.userInfo?[AVAudioSessionRouteChangeReasonKey] as? UInt
            if reason == AVAudioSession.RouteChangeReason.oldDeviceUnavailable.rawValue { Task { @MainActor in self?.pause() } }
        }
        let commands = MPRemoteCommandCenter.shared()
        commands.playCommand.addTarget { [weak self] _ in Task { @MainActor in self?.resume() }; return .success }
        commands.pauseCommand.addTarget { [weak self] _ in Task { @MainActor in self?.pause() }; return .success }
        commands.skipForwardCommand.preferredIntervals = [15]; commands.skipBackwardCommand.preferredIntervals = [15]
        commands.skipForwardCommand.addTarget { [weak self] _ in Task { @MainActor in guard let self else {return}; self.seek(self.position + 15) }; return .success }
        commands.skipBackwardCommand.addTarget { [weak self] _ in Task { @MainActor in guard let self else {return}; self.seek(self.position - 15) }; return .success }
        commands.changePlaybackPositionCommand.addTarget { [weak self] event in guard let event = event as? MPChangePlaybackPositionCommandEvent else { return .commandFailed }; Task { @MainActor in self?.seek(event.positionTime) }; return .success }
    }
    func play(_ podcast: Podcast, store: HarborStore) async {
        if current?.id == podcast.id { resume(); return }
        await sync(); pause(); loading = true; defer { loading = false }
        do {
            let url = try await store.audio(for:podcast)
            self.store = store; current = podcast; duration = podcast.duration_seconds ?? 0; position = podcast.completed ? 0 : podcast.playback_position_seconds
            let item = AVPlayerItem(url:url)
            itemObserver = item.observe(\.status,options:[.new]) { [weak self] item, _ in
                if item.status == .failed { Task { @MainActor in self?.pause(); self?.error = "这段音频暂时无法播放，请移除本机下载后重试。" } }
            }
            player.replaceCurrentItem(with:item); await player.seek(to:CMTime(seconds:position, preferredTimescale:600)); lastSync = position
            setTimer(store.preferences.sleep_timer_minutes); resume()
        } catch { self.error = error.localizedDescription }
    }
    func resume() {
        guard current != nil else { return }
        do { try AVAudioSession.sharedInstance().setCategory(.playback, mode:.default); try AVAudioSession.sharedInstance().setActive(true); if position >= duration && duration > 0 { seek(0) }; player.play(); playing = true; updateNowPlaying() } catch { self.error = error.localizedDescription }
    }
    func pause() { player.pause(); playing = false; updateNowPlaying(); scheduleSync() }
    func seek(_ value: Double) { position = min(max(0,value),max(duration,0)); player.seek(to:CMTime(seconds:position, preferredTimescale:600)); updateNowPlaying(); scheduleSync() }
    func stop() { pause(); player.replaceCurrentItem(with:nil); current = nil; setTimer(0); MPNowPlayingInfoCenter.default().nowPlayingInfo = nil; try? AVAudioSession.sharedInstance().setActive(false, options:.notifyOthersOnDeactivation) }
    private func scheduleSync() { guard let id = current?.id, let store else { return }; let snapshot = position; Task { await store.progress(id:id,position:snapshot) } }
    func sync(completed: Bool = false) async { guard let current, let store else { return }; await store.progress(id:current.id, position:position, completed:completed) }
    func setTimer(_ minutes: Int) {
        timer?.invalidate(); timer = nil; player.volume = 1; timerMinutes = minutes; endOfTrack = minutes == -1; deadline = minutes > 0 ? Date().addingTimeInterval(Double(minutes * 60)) : nil; remaining = max(0, minutes * 60)
        if minutes > 0 { timer = Timer.scheduledTimer(withTimeInterval:1, repeats:true) { [weak self] _ in Task { @MainActor in guard let self, let deadline = self.deadline else {return}; self.remaining = max(0, Int(ceil(deadline.timeIntervalSinceNow))); if self.remaining <= 10 { self.player.volume = Float(self.remaining) / 10 }; if self.remaining == 0 { self.pause(); self.setTimer(0) } } } }
    }
    var timerLabel: String { timerMinutes == -1 ? "本集结束" : timerMinutes == 0 ? "不定时" : clockText(Double(remaining)) }
    private func updateNowPlaying() {
        guard let current else { return }
        MPNowPlayingInfoCenter.default().nowPlayingInfo = [MPMediaItemPropertyTitle:current.title, MPMediaItemPropertyArtist:"夜航 · Night Harbor", MPMediaItemPropertyPlaybackDuration:duration, MPNowPlayingInfoPropertyElapsedPlaybackTime:position, MPNowPlayingInfoPropertyPlaybackRate:playing ? 1.0 : 0.0]
    }
}
