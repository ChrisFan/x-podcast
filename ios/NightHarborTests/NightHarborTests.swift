import XCTest
@testable import NightHarbor

final class NightHarborTests: XCTestCase {
    func testScriptRejectsEmptySegmentsAndWrongVersion() throws {
        XCTAssertThrowsError(try parseScript("{\"version\":1,\"title\":\"night\",\"segments\":[]}"))
        XCTAssertThrowsError(try parseScript("{\"version\":2,\"title\":\"night\",\"segments\":[{\"text\":\"hello\"}]}"))
        XCTAssertThrowsError(try parseScript("[]"))
    }
    func testScriptPreservesNestedControlsAndUnicode() throws {
        let text = "{\"version\":1,\"title\":\"雨夜\",\"mix\":{\"ambience_dbfs\":-38},\"segments\":[{\"text\":\"安静的夜晚\",\"pause_after_seconds\":12}],\"enabled\":true}"
        let parsed = try parseScript(text)
        let roundTrip = try JSONDecoder().decode(JSONValue.self,from:JSONEncoder().encode(parsed))
        XCTAssertEqual(parsed,roundTrip)
    }
    func testAuthenticatedAudioRequestRetainsBasePathAndQuery() throws {
        let api = API(base:URL(string:"https://example.com/podcast/api/")!,token:"test-token")
        let request = try api.request("podcasts/123/audio?variant=mix")
        XCTAssertEqual(request.url?.absoluteString,"https://example.com/podcast/api/podcasts/123/audio?variant=mix")
        XCTAssertEqual(request.value(forHTTPHeaderField:"Authorization"),"Bearer test-token")
        XCTAssertFalse(request.url!.absoluteString.contains("test-token"))
    }
    func testServerErrorsAreShownAndBadResponsesRejected() throws {
        let response = HTTPURLResponse(url:URL(string:"https://example.com")!,statusCode:403,httpVersion:nil,headerFields:nil)!
        XCTAssertThrowsError(try API.check(Data("{\"detail\":\"账户无权访问\"}".utf8),response)) { error in XCTAssertEqual(error.localizedDescription,"账户无权访问") }
    }
    func testDownloadedMediaUsesRecognizableContainerExtension() throws {
        let file = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at:file) }
        try Data("ID3\0\0\0\0\0\0\0\0\0".utf8).write(to:file)
        XCTAssertEqual(try audioFileExtension(for:file),"mp3")
        try Data("RIFF0000WAVE".utf8).write(to:file)
        XCTAssertEqual(try audioFileExtension(for:file),"wav")
        try Data("{\"detail\":\"not audio\"}".utf8).write(to:file)
        XCTAssertThrowsError(try audioFileExtension(for:file))
    }
    func testTimeFormattingSanitizesInvalidMediaDurations() {
        XCTAssertEqual(clockText(.nan),"0:00"); XCTAssertEqual(clockText(-12),"0:00"); XCTAssertEqual(clockText(372),"6:12")
    }
}
