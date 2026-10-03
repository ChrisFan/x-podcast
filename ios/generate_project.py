#!/usr/bin/env python3
"""Generate a dependency-free Xcode project. Run after adding Swift source files."""
from pathlib import Path
import hashlib
ROOT=Path(__file__).resolve().parent
objects={}
def uid(key): return hashlib.sha256(key.encode()).hexdigest()[:24].upper()
def obj(key, value): objects[uid(key)]=value; return uid(key)
def arr(values): return '(' + ', '.join(values) + ',)'
def quote(s): return '"'+str(s).replace('\\','\\\\').replace('"','\\"')+'"'
app_sources=list((ROOT/'NightHarbor').glob('*.swift'))
unit_sources=list((ROOT/'NightHarborTests').glob('*.swift'))
ui_sources=list((ROOT/'NightHarborUITests').glob('*.swift'))
def file(path, type): return obj('file:'+str(path),f'{{isa = PBXFileReference; lastKnownFileType = {type}; path = {quote(path.name)}; sourceTree = "<group>"; }}')
def group(name, files): return obj('group:'+name,f'{{isa = PBXGroup; children = {arr(files)}; path = {quote(name)}; sourceTree = "<group>"; }}')
def phase(name, isa, files): return obj(name,f'{{isa = {isa}; buildActionMask = 2147483647; files = {arr(files) if files else "()"}; runOnlyForDeploymentPostprocessing = 0; }}')
def configs(name, settings):
    ids=[]
    for config in ['Debug','Release']:
        vals={**settings, 'SWIFT_OPTIMIZATION_LEVEL':'-Onone' if config=='Debug' else '-O'}
        if config=='Debug': vals['SWIFT_ACTIVE_COMPILATION_CONDITIONS']='DEBUG'
        cfg=' '.join(f'{k} = {quote(v)};' for k,v in vals.items())
        ids.append(obj('cfg:'+name+config,f'{{isa = XCBuildConfiguration; buildSettings = {{{cfg}}}; name = {config}; }}'))
    return obj('configs:'+name,f'{{isa = XCConfigurationList; buildConfigurations = {arr(ids)}; defaultConfigurationIsVisible = 0; defaultConfigurationName = Release; }}')
groups=[]; products=[]; targets=[]
for name, paths, kind in [('NightHarbor',app_sources,'application'),('NightHarborTests',unit_sources,'bundle.unit-test'),('NightHarborUITests',ui_sources,'bundle.ui-testing')]:
    refs=[]; builds=[]
    for path in paths:
        r=file(path,'sourcecode.swift'); refs.append(r); builds.append(obj('build:'+str(path),f'{{isa = PBXBuildFile; fileRef = {r}; }}'))
    resources=[]
    if name=='NightHarbor':
        for path, typ in [(ROOT/name/'sample-script.json','text.json'),(ROOT/name/'Info.plist','text.plist.xml'),(ROOT/name/'PrivacyInfo.xcprivacy','text.xml'),(ROOT/name/'Assets.xcassets','folder.assetcatalog')]:
            r=file(path,typ); refs.append(r)
            if path.suffix in ['.json','.xcassets','.xcprivacy']: resources.append(obj('resource:'+str(path),f'{{isa = PBXBuildFile; fileRef = {r}; }}'))
    groups.append(group(name,refs))
    product=obj('product:'+name,f'{{isa = PBXFileReference; explicitFileType = {"wrapper.application" if name=="NightHarbor" else "wrapper.cfbundle"}; path = {name}{".app" if name=="NightHarbor" else ".xctest"}; sourceTree = BUILT_PRODUCTS_DIR; }}'); products.append(product)
    settings={'PRODUCT_NAME':'$(TARGET_NAME)','PRODUCT_BUNDLE_IDENTIFIER':'com.pawlpixel.'+name,'SWIFT_VERSION':'5.0','IPHONEOS_DEPLOYMENT_TARGET':'17.0','TARGETED_DEVICE_FAMILY':'1','CODE_SIGN_STYLE':'Automatic','DEVELOPMENT_TEAM':'DXH9X9Y868','MARKETING_VERSION':'0.1.0','CURRENT_PROJECT_VERSION':'1','GENERATE_INFOPLIST_FILE':'YES','DEBUG_INFORMATION_FORMAT':'dwarf-with-dsym'}
    if name=='NightHarbor': settings.update({'GENERATE_INFOPLIST_FILE':'NO','INFOPLIST_FILE':'NightHarbor/Info.plist','ASSETCATALOG_COMPILER_APPICON_NAME':'AppIcon'})
    if name=='NightHarborTests': settings.update({'TEST_HOST':'$(BUILT_PRODUCTS_DIR)/NightHarbor.app/$(BUNDLE_EXECUTABLE_FOLDER_PATH)/NightHarbor','BUNDLE_LOADER':'$(TEST_HOST)'})
    if name=='NightHarborUITests': settings['TEST_TARGET_NAME']='NightHarbor'
    deps=[]
    if name!='NightHarbor':
        proxy=obj('proxy:'+name,f'{{isa = PBXContainerItemProxy; containerPortal = {uid("project")}; proxyType = 1; remoteGlobalIDString = {uid("target:NightHarbor")}; remoteInfo = NightHarbor; }}')
        deps=[obj('dep:'+name,f'{{isa = PBXTargetDependency; target = {uid("target:NightHarbor")}; targetProxy = {proxy}; }}')]
    phases=[phase('sources:'+name,'PBXSourcesBuildPhase',builds),phase('resources:'+name,'PBXResourcesBuildPhase',resources),phase('frameworks:'+name,'PBXFrameworksBuildPhase',[])]
    targets.append(obj('target:'+name,f'{{isa = PBXNativeTarget; buildConfigurationList = {configs(name,settings)}; buildPhases = {arr(phases)}; buildRules = (); dependencies = {arr(deps) if deps else "()"}; name = {name}; productName = {name}; productReference = {product}; productType = "com.apple.product-type.{kind}"; }}'))
productsGroup=obj('products',f'{{isa = PBXGroup; children = {arr(products)}; name = Products; sourceTree = "<group>"; }}')
mainGroup=obj('main',f'{{isa = PBXGroup; children = {arr(groups+[productsGroup])}; sourceTree = "<group>"; }}')
projectConfig=configs('project',{'SDKROOT':'iphoneos','CLANG_ENABLE_MODULES':'YES','SWIFT_VERSION':'5.0','ENABLE_TESTABILITY':'YES','IPHONEOS_DEPLOYMENT_TARGET':'17.0'})
obj('project',f'{{isa = PBXProject; attributes = {{LastUpgradeCheck = 2700;}}; buildConfigurationList = {projectConfig}; compatibilityVersion = "Xcode 14.0"; developmentRegion = zh_CN; hasScannedForEncodings = 0; knownRegions = (zh_CN, en, Base); mainGroup = {mainGroup}; productRefGroup = {productsGroup}; projectDirPath = ""; projectRoot = ""; targets = {arr(targets)}; }}')
project=ROOT/'NightHarbor.xcodeproj'; project.mkdir(exist_ok=True)
(project/'project.pbxproj').write_text('// !$*UTF8*$!\n{ archiveVersion = 1; classes = {}; objectVersion = 56; objects = {\n'+'\n'.join(f'{key} = {value};' for key,value in objects.items())+f'\n}}; rootObject = {uid("project")}; }}\n')
scheme=project/'xcshareddata/xcschemes'; scheme.mkdir(parents=True,exist_ok=True)
def ref(name): return f'<BuildableReference BuildableIdentifier="primary" BlueprintIdentifier="{uid("target:"+name)}" BuildableName="{name}{".app" if name=="NightHarbor" else ".xctest"}" BlueprintName="{name}" ReferencedContainer="container:NightHarbor.xcodeproj"/>'
(scheme/'NightHarbor.xcscheme').write_text(f'''<?xml version="1.0" encoding="UTF-8"?>
<Scheme LastUpgradeVersion="2700" version="1.3"><BuildAction parallelizeBuildables="YES" buildImplicitDependencies="YES"><BuildActionEntries><BuildActionEntry buildForTesting="YES" buildForRunning="YES" buildForProfiling="YES" buildForArchiving="YES" buildForAnalyzing="YES">{ref('NightHarbor')}</BuildActionEntry></BuildActionEntries></BuildAction><TestAction buildConfiguration="Debug" selectedDebuggerIdentifier="Xcode.DebuggerFoundation.Debugger.LLDB" selectedLauncherIdentifier="Xcode.IDEFoundation.Launcher.LLDB" shouldUseLaunchSchemeArgsEnv="YES"><Testables><TestableReference skipped="NO">{ref('NightHarborTests')}</TestableReference><TestableReference skipped="NO">{ref('NightHarborUITests')}</TestableReference></Testables></TestAction><LaunchAction buildConfiguration="Debug" selectedDebuggerIdentifier="Xcode.DebuggerFoundation.Debugger.LLDB" selectedLauncherIdentifier="Xcode.IDEFoundation.Launcher.LLDB" launchStyle="0" useCustomWorkingDirectory="NO" ignoresPersistentStateOnLaunch="NO" debugServiceExtension="internal" allowLocationSimulation="YES"><BuildableProductRunnable runnableDebuggingMode="0">{ref('NightHarbor')}</BuildableProductRunnable></LaunchAction><ProfileAction buildConfiguration="Release" shouldUseLaunchSchemeArgsEnv="YES" savedToolIdentifier="" useCustomWorkingDirectory="NO" debugServiceExtension="internal"><BuildableProductRunnable runnableDebuggingMode="0">{ref('NightHarbor')}</BuildableProductRunnable></ProfileAction><AnalyzeAction buildConfiguration="Debug"/><ArchiveAction buildConfiguration="Release" revealArchiveInOrganizer="YES"/></Scheme>''')
print(project)
