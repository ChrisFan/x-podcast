import AppKit
let size = CGSize(width:1024,height:1024)
let bitmap = NSBitmapImageRep(bitmapDataPlanes:nil,pixelsWide:1024,pixelsHigh:1024,bitsPerSample:8,samplesPerPixel:4,hasAlpha:true,isPlanar:false,colorSpaceName:.deviceRGB,bytesPerRow:0,bitsPerPixel:0)!
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep:bitmap)
NSColor(calibratedRed:0.045,green:0.065,blue:0.12,alpha:1).setFill()
NSBezierPath(rect:NSRect(origin:.zero,size:size)).fill()
NSColor(calibratedRed:0.64,green:0.76,blue:0.69,alpha:1).setFill()
NSBezierPath(ovalIn:NSRect(x:244,y:288,width:450,height:450)).fill()
NSColor(calibratedRed:0.045,green:0.065,blue:0.12,alpha:1).setFill()
NSBezierPath(ovalIn:NSRect(x:335,y:370,width:410,height:410)).fill()
NSColor(calibratedRed:0.93,green:0.91,blue:0.84,alpha:1).setFill()
let star=NSBezierPath(); star.move(to:NSPoint(x:740,y:704)); star.line(to:NSPoint(x:757,y:747)); star.line(to:NSPoint(x:800,y:764)); star.line(to:NSPoint(x:757,y:781)); star.line(to:NSPoint(x:740,y:824)); star.line(to:NSPoint(x:723,y:781)); star.line(to:NSPoint(x:680,y:764)); star.line(to:NSPoint(x:723,y:747)); star.close(); star.fill()
let wave=NSBezierPath(); wave.move(to:NSPoint(x:232,y:228)); wave.curve(to:NSPoint(x:792,y:228),controlPoint1:NSPoint(x:410,y:156),controlPoint2:NSPoint(x:610,y:300)); wave.lineWidth=13; wave.lineCapStyle = .round; NSColor(calibratedRed:0.64,green:0.76,blue:0.69,alpha:0.7).setStroke(); wave.stroke()
NSGraphicsContext.restoreGraphicsState()
let data=bitmap.representation(using:.png,properties:[:])!
try data.write(to:URL(fileURLWithPath:CommandLine.arguments[1]))
