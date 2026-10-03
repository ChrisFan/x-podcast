import XCTest

final class NightHarborUITests: XCTestCase {
    override func setUpWithError() throws { continueAfterFailure = false }
    @MainActor private func capture(_ app: XCUIApplication, _ name: String) { let attachment = XCTAttachment(screenshot:app.screenshot()); attachment.name = name; attachment.lifetime = .keepAlways; add(attachment) }
    @MainActor private func assertPlayback(_ app: XCUIApplication, playing: Bool, timeout: TimeInterval) {
        let state = XCTNSPredicateExpectation(predicate:NSPredicate(format:"exists == true AND label == %@",playing ? "暂停" : "播放"),object:app.buttons["playerToggle"])
        XCTAssertEqual(XCTWaiter.wait(for:[state],timeout:timeout),.completed)
    }
    @MainActor func testOnboardingAndServerConfiguration() throws {
        let app = XCUIApplication(); app.launchArguments = ["--uitest-reset"]; app.launch()
        XCTAssertTrue(app.textFields["email"].waitForExistence(timeout:10))
        XCTAssertTrue(app.secureTextFields["password"].exists)
        app.buttons["服务器"].tap()
        XCTAssertTrue(app.navigationBars["服务器设置"].waitForExistence(timeout:3))
        app.buttons["取消"].tap()
        let shot = XCTAttachment(screenshot:app.screenshot()); shot.name = "Onboarding"; shot.lifetime = .keepAlways; add(shot)
    }
    @MainActor private func authenticatedLiveApp() throws -> XCUIApplication {
        let env = ProcessInfo.processInfo.environment
        guard let email = env["NIGHT_HARBOR_TEST_EMAIL"], let password = env["NIGHT_HARBOR_TEST_PASSWORD"] else { throw XCTSkip("Live acceptance requires a dedicated test account via xctestrun environment.") }
        addUIInterruptionMonitor(withDescription:"Password autofill") { alert in
            if alert.buttons["Not Now"].exists { alert.buttons["Not Now"].tap(); return true }
            if alert.buttons["以后"].exists { alert.buttons["以后"].tap(); return true }
            return false
        }
        let app = XCUIApplication(); app.launchArguments = ["--uitest-reset", "--api-base", env["NIGHT_HARBOR_TEST_API"] ?? "https://alu-designer.pawlpixel.com/podcast/api"]; app.launch()
        let emailField = app.textFields["email"]; XCTAssertTrue(emailField.waitForExistence(timeout:10)); emailField.tap(); emailField.typeText(email)
        let passwordField = app.secureTextFields["password"]; passwordField.tap(); passwordField.typeText(password)
        app.buttons["authenticate"].tap()
        XCTAssertTrue(app.tabBars.buttons["我的播客"].waitForExistence(timeout:30))
        let springboard = XCUIApplication(bundleIdentifier:"com.apple.springboard")
        if springboard.buttons["Not Now"].waitForExistence(timeout:3) { springboard.buttons["Not Now"].tap() }
        else if app.buttons["Not Now"].waitForExistence(timeout:8) { app.buttons["Not Now"].tap() }
        XCTAssertTrue(app.buttons["Not Now"].waitForNonExistence(timeout:5))
        return app
    }
    @MainActor func testLiveMiniPlayerNavigation() throws {
        let env = ProcessInfo.processInfo.environment
        guard env["NIGHT_HARBOR_TEST_READY_TITLE"] != nil else { throw XCTSkip("Requires a ready episode.") }
        let app = try authenticatedLiveApp()
        if env["NIGHT_HARBOR_TEST_READY_TITLE"] != nil {
            let start = app.buttons["开始今晚"]
            XCTAssertTrue(start.waitForExistence(timeout:10)); start.tap()
            XCTAssertTrue(app.buttons["收起播放器"].waitForExistence(timeout:120))
            app.buttons["收起播放器"].tap()
            let miniPlayer = app.buttons["miniPlayerOpen"]
            XCTAssertTrue(miniPlayer.waitForExistence(timeout:5))
            for name in ["我的播客", "我的", "今晚"] {
                let tab = app.tabBars.buttons[name]
                XCTAssertTrue(tab.isHittable, "Playback must not block the \(name) tab")
                XCTAssertLessThanOrEqual(miniPlayer.frame.maxY, tab.frame.minY, "Mini player must stay above the tab buttons")
                tab.tap()
                XCTAssertTrue(tab.isSelected, "Tapping \(name) must switch tabs")
            }
            capture(app,"Mini player above tabs")
            miniPlayer.tap()
            XCTAssertTrue(app.buttons["收起播放器"].waitForExistence(timeout:5))
            app.buttons["收起播放器"].tap()
        }
    }
    @MainActor func testLiveAccountDraftAndPlayback() throws {
        let env = ProcessInfo.processInfo.environment
        let app = try authenticatedLiveApp()
        capture(app,"Tonight")
        app.tabBars.buttons["我的播客"].coordinate(withNormalizedOffset:CGVector(dx:0.5,dy:0.5)).tap(); XCTAssertTrue(app.navigationBars["我的播客"].waitForExistence(timeout:5)); app.buttons["制作播客"].firstMatch.coordinate(withNormalizedOffset:CGVector(dx:0.5,dy:0.5)).tap()
        XCTAssertTrue(app.navigationBars["制作一段夜晚"].waitForExistence(timeout:5))
        capture(app,"Editor")
        let titleField = app.textFields["播客标题"]; titleField.tap()
        if let value = titleField.value as? String { titleField.typeText(String(repeating:XCUIKeyboardKey.delete.rawValue,count:value.count)) }
        titleField.typeText("iOS Acceptance Draft")
        app.buttons["saveDraft"].coordinate(withNormalizedOffset:CGVector(dx:0.5,dy:0.5)).tap()
        XCTAssertTrue(app.navigationBars["我的播客"].waitForExistence(timeout:15))
        capture(app,"Library")
        let draft = app.buttons.containing(.staticText,identifier:"iOS Acceptance Draft").firstMatch
        XCTAssertTrue(draft.waitForExistence(timeout:10)); draft.tap()
        XCTAssertTrue(app.buttons["编辑脚本与听感"].waitForExistence(timeout:5))
        let draftShot = XCTAttachment(screenshot:app.screenshot()); draftShot.name = "Live draft lifecycle"; draftShot.lifetime = .keepAlways; add(draftShot)
        app.swipeUp(); app.buttons["删除播客"].tap(); app.buttons.matching(identifier:"删除播客").allElementsBoundByIndex.first(where:{$0.isHittable})?.tap()
        XCTAssertTrue(app.navigationBars["我的播客"].waitForExistence(timeout:10))
        if let title = env["NIGHT_HARBOR_TEST_READY_TITLE"] {
            app.buttons.containing(.staticText,identifier:title).firstMatch.tap()
            app.buttons["继续收听"].tap()
            assertPlayback(app,playing:true,timeout:120)
            app.buttons["前进 15 秒"].tap()
            app.buttons["sleepTimer"].tap(); app.buttons["本集结束"].tap()
            XCTAssertTrue(app.buttons["sleepTimer"].label.contains("本集结束"))
            let beforeBackground = app.staticTexts["playbackElapsed"].label
            XCUIDevice.shared.press(.home)
            Thread.sleep(forTimeInterval:3)
            app.activate()
            XCTAssertNotEqual(app.staticTexts["playbackElapsed"].label,beforeBackground)
            assertPlayback(app,playing:true,timeout:10)
            let shot = XCTAttachment(screenshot:app.screenshot()); shot.name = "Live player"; shot.lifetime = .keepAlways; add(shot)
            app.buttons["收起播放器"].tap()
            app.buttons.containing(.staticText,identifier:"MCP 验收 · 窗边雨声").firstMatch.tap()
            app.buttons["继续收听"].tap()
            let shortEpisodeProgress = app.sliders["播放进度"]
            XCTAssertTrue(shortEpisodeProgress.waitForExistence(timeout:30))
            // This live account may already have progress from another test run.
            let fullPlayerToggle = app.buttons["playerToggle"]
            if fullPlayerToggle.label == "暂停" { fullPlayerToggle.tap() }
            let paused = XCTNSPredicateExpectation(predicate:NSPredicate(format:"label == %@","播放"),object:fullPlayerToggle)
            XCTAssertEqual(XCTWaiter.wait(for:[paused],timeout:5),.completed)
            shortEpisodeProgress.adjust(toNormalizedSliderPosition:0)
            fullPlayerToggle.tap()
            assertPlayback(app,playing:true,timeout:5)
            app.buttons["sleepTimer"].tap(); app.buttons["本集结束"].tap()
            let ended = XCTNSPredicateExpectation(predicate:NSPredicate(format:"label == %@","0:20"),object:app.staticTexts["playbackElapsed"])
            XCTAssertEqual(XCTWaiter.wait(for:[ended],timeout:35),.completed)
            assertPlayback(app,playing:false,timeout:5)
            XCTAssertTrue(app.buttons["sleepTimer"].label.contains("不定时"))
            capture(app,"End of track stopped")
            app.terminate()
            app.launchArguments = ["--uitest-offline"]; app.launch()
            XCTAssertTrue(app.staticTexts["暂时无法连接 · 已下载的内容仍可收听"].waitForExistence(timeout:10))
            app.tabBars.buttons["我的播客"].coordinate(withNormalizedOffset:CGVector(dx:0.5,dy:0.5)).tap()
            app.buttons.containing(.staticText,identifier:title).firstMatch.tap()
            XCTAssertTrue(app.staticTexts["已下载 · 可离线收听"].waitForExistence(timeout:5))
            app.buttons["继续收听"].tap()
            assertPlayback(app,playing:true,timeout:15)
            let offlineStart = app.staticTexts["playbackElapsed"].label
            let advancing = XCTNSPredicateExpectation(predicate:NSPredicate(format:"label != %@",offlineStart),object:app.staticTexts["playbackElapsed"])
            XCTAssertEqual(XCTWaiter.wait(for:[advancing],timeout:8),.completed)
            let offline = XCTAttachment(screenshot:app.screenshot()); offline.name = "Offline cached player"; offline.lifetime = .keepAlways; add(offline)
            app.terminate(); app.launchArguments = []; app.launch()
            XCTAssertTrue(app.tabBars.buttons["我的"].waitForExistence(timeout:10)); app.tabBars.buttons["我的"].coordinate(withNormalizedOffset:CGVector(dx:0.5,dy:0.5)).tap()
            app.swipeUp(); app.buttons["退出登录"].tap(); app.buttons.matching(identifier:"退出登录").allElementsBoundByIndex.first(where:{$0.isHittable})?.tap()
            XCTAssertTrue(app.textFields["email"].waitForExistence(timeout:10))
            XCTAssertFalse(app.tabBars.buttons["我的播客"].exists)
            XCTAssertFalse(app.staticTexts[title].exists)
            let loggedOut = XCTAttachment(screenshot:app.screenshot()); loggedOut.name = "Logout hides cached library"; loggedOut.lifetime = .keepAlways; add(loggedOut)
        }
    }
}
