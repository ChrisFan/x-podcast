# 夜航 iPhone Beta 发布

日期：2026-10-03。使用 Zheng Fan 的个人 Team `DXH9X9Y868`。

| 项目 | 值 |
| --- | --- |
| App 名称 | 夜航 - 睡眠播客 |
| Apple ID | `6818797321` |
| Bundle ID | `com.pawlpixel.NightHarbor` |
| SKU / 主语言 | `nightharbor-ios-001` / `zh-Hans` |
| Beta 版本 | `0.1.0 (1)` |
| 内部测试组 | 夜航内部 Beta，`79961264-ffee-4dea-aac0-d01d52d0be41` |
| App Store Connect | https://appstoreconnect.apple.com/apps/6818797321/distribution |
| TestFlight | https://appstoreconnect.apple.com/teams/755d8b41-2e01-4409-94e9-7dbbae3b043f/apps/6818797321/testflight |

已完成 App 记录创建、个人团队专用 Bundle ID、Release 归档、App Store 分发签名导出、Xcode 上传。上传于北京时间 21:46 成功，Apple 已处理为 `VALID`，内部状态 `READY_FOR_BETA_TESTING`。构建已分配至内部测试组，网页显示 **Ready to Test**，中文测试说明已保存；已按用户指定邀请 `chris.fan.robot@gmail.com`，网页及 API 均确认状态为 `INVITED`，组内现有 1 位测试者。邀请截图见 `acceptance/testflight-invited.png`；尚未验证邮件收件或真机安装。构建 UUID 为 `66b433af-36bf-4980-942d-592d4ea030d3`，证据见 `acceptance/beta-release.json`。

## 签名与凭据边界

`~/.config/aipodcast/appstoreconnect/config.json` 是本 App 的独立私密配置，目录 700、文件 600，引用已有 Individual Key 路径；没有复制私钥、撤销密钥或覆盖 Waterline 配置。API 验证通过，并核对 Apple ID、Bundle ID、SKU 和语言。

机器人账号只用于 App Store Connect 管理；个人会员下该账号无法直接访问 Developer Program 的证书/标识资源。实际归档与上传使用 Xcode 已登录的个人团队账号及本机证书。导出的 profile 为 `iOS Team Store Provisioning Profile: com.pawlpixel.NightHarbor`，application-identifier 为 `DXH9X9Y868.com.pawlpixel.NightHarbor`，`get-task-allow=false`。

本机 Xcode 27 的 altool 在 Individual Key 验证时仍要求 issuer ID，未采用虚构 issuer 或重新生成密钥；本次改用 Xcode 自身的上传链路并成功。API 管理和构建上传是分别验证的两条链路。

## 构建与上传

```sh
python3 ios/generate_project.py
xcodebuild -project ios/NightHarbor.xcodeproj -scheme NightHarbor \
  -configuration Release -destination 'generic/platform=iOS' \
  -archivePath ios/build/release/NightHarbor-0.1.0-1.xcarchive \
  -derivedDataPath ios/build/release-derived -allowProvisioningUpdates archive
python3 ios/release/transfer.py export
# 只有新构建才再次上传；已成功上传的同一版本/build 不要重复发送
python3 ios/release/transfer.py upload
```

IPA：`ios/build/release/export/NightHarbor.ipa`。版本号与 build 在 `ios/generate_project.py` 中维护；下次递增 build，再生成工程，按对应 archive 路径传给 `transfer.py --archive`。

`ios/release/asc.mjs` 使用短期 JWT，默认读取夜航配置，并检查其目标标识；不输出私钥或 JWT。写操作没有自动重试，网络结果不明时先查询实际状态，避免重复创建。

```sh
node ios/release/asc.mjs '/v1/apps/6818797321/builds?limit=20'
node ios/release/asc.mjs '/v1/apps/6818797321/betaGroups?limit=50'
```

## 本次发布配置

- App 只使用系统 HTTPS、Keychain 与 CryptoKit 哈希，无自行实现的非豁免加密；Info.plist 标明不使用非豁免加密。
- 加入 `PrivacyInfo.xcprivacy`：UserDefaults 仅保存本 App 的服务器地址，声明 CA92.1 原因；没有广告跟踪。
- 本 App 的账户、脚本、生成结果和收听进度会存储在云端；不能套用 Waterline 的“离线、不收集数据”声明。正式 App Store 隐私问卷尚未提交。
- TestFlight Beta 与 App Store 正式发布分开。本次不提交 App Store 审核，不开放公开测试链接，不自动邀请其他团队成员。
- 没有连接实体 iPhone，因此“实际在用户手机安装并收听”仍需用户完成；此前仅有模拟器后台/离线播放验收。TestFlight 处理完成不等于完成真机体验验收。

参考用户提供的 `Waterline/Docs/APP_STORE_AUTOMATION_HANDOFF_CN.md`，以及 [Apple TestFlight 工作流程](https://developer.apple.com/help/app-store-connect/test-a-beta-version/testflight-overview/)。
