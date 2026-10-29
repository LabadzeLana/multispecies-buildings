// Web copies for "A City of Vineyards" (macOS only: ImageIO + AVFoundation, no extra installs).
//
//   encode image  <in> <out.jpg> <maxLongEdge> <quality 0-1>
//        sRGB, EXIF orientation applied, ALL metadata dropped, never upscaled. Prints "w h".
//   encode video  <in> <out.mp4> <maxW> <maxH> <videoKbps> <audio 0|1> [start s] [duration s]
//        H.264 High + AAC 128 kb/s (stereo track only), moov first (faststart), no metadata.
//   encode poster <in-video> <out.jpg> <time s> <maxLongEdge> <quality>
//   encode frames <in-video> <outPrefix> <t1> <t2> ...      (for looking at a video)
import Foundation
import AVFoundation
import ImageIO
import CoreGraphics
import UniformTypeIdentifiers

let A = CommandLine.arguments
func fail(_ s: String) -> Never { FileHandle.standardError.write((s + "\n").data(using: .utf8)!); exit(1) }

func writeJPEG(_ img: CGImage, _ out: String, _ q: Double) {
  // redraw into sRGB so every copy has the same colour space and carries nothing but pixels
  let cs = CGColorSpace(name: CGColorSpace.sRGB)!
  let ctx = CGContext(data: nil, width: img.width, height: img.height, bitsPerComponent: 8, bytesPerRow: 0,
                      space: cs, bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue)!
  ctx.setFillColor(CGColor(red: 1, green: 1, blue: 1, alpha: 1)); ctx.fill(CGRect(x: 0, y: 0, width: img.width, height: img.height))
  ctx.draw(img, in: CGRect(x: 0, y: 0, width: img.width, height: img.height))
  let d = CGImageDestinationCreateWithURL(URL(fileURLWithPath: out) as CFURL, UTType.jpeg.identifier as CFString, 1, nil)!
  CGImageDestinationAddImage(d, ctx.makeImage()!, [kCGImageDestinationLossyCompressionQuality: q,
                                                   kCGImagePropertyJFIFDictionary: [kCGImagePropertyJFIFIsProgressive: true]] as CFDictionary)
  if !CGImageDestinationFinalize(d) { fail("could not write \(out)") }
}

func image(_ inp: String, _ out: String, _ maxPx: Int, _ q: Double) {
  guard let src = CGImageSourceCreateWithURL(URL(fileURLWithPath: inp) as CFURL, nil) else { fail("cannot read \(inp)") }
  let props = CGImageSourceCopyPropertiesAtIndex(src, 0, nil) as? [CFString: Any] ?? [:]
  var w = props[kCGImagePropertyPixelWidth] as? Int ?? 0, h = props[kCGImagePropertyPixelHeight] as? Int ?? 0
  if let o = props[kCGImagePropertyOrientation] as? Int, o >= 5 { swap(&w, &h) }
  let target = min(maxPx, max(w, h))   // never upscale
  let img = CGImageSourceCreateThumbnailAtIndex(src, 0, [kCGImageSourceCreateThumbnailFromImageAlways: true,
    kCGImageSourceCreateThumbnailWithTransform: true, kCGImageSourceThumbnailMaxPixelSize: target] as CFDictionary)!
  writeJPEG(img, out, q)
  print(img.width, img.height)
}

func poster(_ inp: String, _ out: String, _ t: Double, _ maxPx: Int, _ q: Double) {
  let g = AVAssetImageGenerator(asset: AVURLAsset(url: URL(fileURLWithPath: inp)))
  g.appliesPreferredTrackTransform = true
  g.requestedTimeToleranceBefore = .zero; g.requestedTimeToleranceAfter = .zero
  g.maximumSize = CGSize(width: maxPx, height: maxPx)
  let cg = try! g.copyCGImage(at: CMTime(seconds: t, preferredTimescale: 600), actualTime: nil)
  writeJPEG(cg, out, q)
  print(cg.width, cg.height)
}

func video(_ inp: String, _ out: String, _ maxW: Int, _ maxH: Int, _ kbps: Int, _ withAudio: Bool, _ start: Double, _ dur: Double) {
  let asset = AVURLAsset(url: URL(fileURLWithPath: inp))
  guard let vt = asset.tracks(withMediaType: .video).first else { fail("no video track") }
  let nat = vt.naturalSize.applying(vt.preferredTransform)
  let sw = abs(nat.width), sh = abs(nat.height)
  let k = min(1, min(Double(maxW) / sw, Double(maxH) / sh))
  let ow = Int((sw * k / 2).rounded()) * 2, oh = Int((sh * k / 2).rounded()) * 2
  let total = asset.duration.seconds
  let range = CMTimeRange(start: CMTime(seconds: start, preferredTimescale: 600),
                          duration: CMTime(seconds: dur > 0 ? min(dur, total - start) : total - start, preferredTimescale: 600))
  try? FileManager.default.removeItem(atPath: out)
  let reader = try! AVAssetReader(asset: asset); reader.timeRange = range
  let writer = try! AVAssetWriter(outputURL: URL(fileURLWithPath: out), fileType: .mp4)
  writer.shouldOptimizeForNetworkUse = true   // moov atom first
  writer.metadata = []
  let vOut = AVAssetReaderTrackOutput(track: vt, outputSettings: [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange])
  reader.add(vOut)
  let vIn = AVAssetWriterInput(mediaType: .video, outputSettings: [
    AVVideoCodecKey: AVVideoCodecType.h264, AVVideoWidthKey: ow, AVVideoHeightKey: oh,
    AVVideoScalingModeKey: AVVideoScalingModeResizeAspectFill,
    AVVideoCompressionPropertiesKey: [AVVideoAverageBitRateKey: kbps * 1000, AVVideoProfileLevelKey: AVVideoProfileLevelH264HighAutoLevel,
                                      AVVideoMaxKeyFrameIntervalDurationKey: 2, AVVideoAllowFrameReorderingKey: true]])
  vIn.transform = vt.preferredTransform
  vIn.expectsMediaDataInRealTime = false
  writer.add(vIn)
  var aOut: AVAssetReaderTrackOutput? = nil, aIn: AVAssetWriterInput? = nil
  if withAudio, let at = asset.tracks(withMediaType: .audio).first(where: { t in
      (t.formatDescriptions as! [CMFormatDescription]).contains { CMAudioFormatDescriptionGetStreamBasicDescription($0)?.pointee.mChannelsPerFrame ?? 0 <= 2 } }) {
    let o = AVAssetReaderTrackOutput(track: at, outputSettings: [AVFormatIDKey: kAudioFormatLinearPCM, AVNumberOfChannelsKey: 2, AVSampleRateKey: 48000])
    reader.add(o); aOut = o
    let i = AVAssetWriterInput(mediaType: .audio, outputSettings: [AVFormatIDKey: kAudioFormatMPEG4AAC, AVNumberOfChannelsKey: 2,
                                                                  AVSampleRateKey: 48000, AVEncoderBitRateKey: 128000])
    i.expectsMediaDataInRealTime = false; writer.add(i); aIn = i
  }
  reader.startReading(); writer.startWriting(); writer.startSession(atSourceTime: range.start)
  let group = DispatchGroup()
  func pump(_ input: AVAssetWriterInput, _ output: AVAssetReaderTrackOutput, _ q: String) {
    group.enter()
    input.requestMediaDataWhenReady(on: DispatchQueue(label: q)) {
      while input.isReadyForMoreMediaData {
        if let b = output.copyNextSampleBuffer() { input.append(b) } else { input.markAsFinished(); group.leave(); return }
      }
    }
  }
  pump(vIn, vOut, "v"); if let i = aIn, let o = aOut { pump(i, o, "a") }
  group.wait()
  let sem = DispatchSemaphore(value: 0); writer.finishWriting { sem.signal() }; sem.wait()
  if writer.status != .completed { fail("write failed: \(String(describing: writer.error))") }
  print(ow, oh, String(format: "%.2f", range.duration.seconds))
}

switch A.count > 1 ? A[1] : "" {
case "image": image(A[2], A[3], Int(A[4])!, Double(A[5])!)
case "poster": poster(A[2], A[3], Double(A[4])!, Int(A[5])!, Double(A[6])!)
case "video": video(A[2], A[3], Int(A[4])!, Int(A[5])!, Int(A[6])!, A[7] == "1", A.count > 8 ? Double(A[8])! : 0, A.count > 9 ? Double(A[9])! : 0)
case "frames": for t in A.dropFirst(4) { poster(A[2], A[3] + "_" + t + ".jpg", Double(t)!, 900, 0.8) }
default: fail("usage: encode image|video|poster|frames ...")
}
