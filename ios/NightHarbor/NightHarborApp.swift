import SwiftUI

@main struct NightHarborApp: App {
    @StateObject private var store = HarborStore()
    @StateObject private var player = SleepPlayer()
    @Environment(\.scenePhase) private var phase
    var body: some Scene {
        WindowGroup { RootView().environmentObject(store).environmentObject(player).onChange(of:phase) { _, value in if value == .active { store.startPolling() } else { store.stopPolling(); Task { await player.sync() } } } }
    }
}
