import SwiftUI
import AVKit

struct VideoPlayerView: View {
    let videoURL: URL
    let startTime: Double? // 起始时间（秒）

    @State private var player: AVPlayer?
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack(spacing: 0) {
            // 顶部工具栏
            HStack {
                Text("视频播放")
                    .font(.headline)

                Spacer()

                if let startTime = startTime {
                    Text("跳转到: \(formatTime(startTime))")
                        .font(.caption)
                        .foregroundColor(.blue)
                }

                Button(action: { dismiss() }) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(.gray)
                }
                .buttonStyle(.plain)
            }
            .padding()
            .background(Color(NSColor.controlBackgroundColor))

            // 视频播放器
            if let player = player {
                VideoPlayer(player: player)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                ProgressView("加载视频中...")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
        .frame(width: 800, height: 600)
        .onAppear {
            setupPlayer()
        }
        .onDisappear {
            player?.pause()
        }
    }

    private func setupPlayer() {
        let player = AVPlayer(url: videoURL)
        self.player = player

        // 如果指定了起始时间，跳转到该位置
        if let startTime = startTime {
            let time = CMTime(seconds: startTime, preferredTimescale: 600)
            player.seek(to: time) { _ in
                player.play()
            }
        } else {
            player.play()
        }
    }

    private func formatTime(_ seconds: Double) -> String {
        let hours = Int(seconds) / 3600
        let minutes = Int(seconds) % 3600 / 60
        let secs = Int(seconds) % 60
        return String(format: "%02d:%02d:%02d", hours, minutes, secs)
    }
}

struct AudioPlayerView: View {
    let audioURL: URL
    let startTime: Double?

    @State private var player: AVPlayer?
    @State private var isPlaying = false
    @State private var currentTime: Double = 0
    @State private var duration: Double = 0
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack(spacing: 20) {
            // 顶部
            HStack {
                Text("音频播放")
                    .font(.headline)
                Spacer()
                Button(action: { dismiss() }) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(.gray)
                }
                .buttonStyle(.plain)
            }

            Spacer()

            // 音频图标
            Image(systemName: "waveform.circle.fill")
                .font(.system(size: 100))
                .foregroundColor(.purple)

            // 文件名
            Text(audioURL.lastPathComponent)
                .font(.headline)

            // 进度条
            VStack(spacing: 8) {
                Slider(value: Binding(
                    get: { currentTime },
                    set: { newValue in
                        currentTime = newValue
                        seekToTime(newValue)
                    }
                ), in: 0...max(duration, 1))

                HStack {
                    Text(formatTime(currentTime))
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Spacer()
                    Text(formatTime(duration))
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            .padding(.horizontal)

            // 播放控制
            HStack(spacing: 40) {
                // 后退 10 秒
                Button(action: { seekRelative(-10) }) {
                    Image(systemName: "gobackward.10")
                        .font(.title2)
                }
                .buttonStyle(.plain)

                // 播放/暂停
                Button(action: togglePlayPause) {
                    Image(systemName: isPlaying ? "pause.circle.fill" : "play.circle.fill")
                        .font(.system(size: 50))
                }
                .buttonStyle(.plain)

                // 前进 10 秒
                Button(action: { seekRelative(10) }) {
                    Image(systemName: "goforward.10")
                        .font(.title2)
                }
                .buttonStyle(.plain)
            }

            Spacer()
        }
        .padding()
        .frame(width: 400, height: 400)
        .onAppear {
            setupPlayer()
        }
        .onDisappear {
            player?.pause()
        }
    }

    private func setupPlayer() {
        let player = AVPlayer(url: audioURL)
        self.player = player

        // 获取时长
        if let asset = player.currentItem?.asset {
            Task {
                if let duration = try? await asset.load(.duration) {
                    self.duration = duration.seconds
                }
            }
        }

        // 监听播放进度
        player.addPeriodicTimeObserver(forInterval: CMTime(seconds: 0.5, preferredTimescale: 600), queue: .main) { time in
            currentTime = time.seconds
        }

        // 如果指定了起始时间，跳转到该位置
        if let startTime = startTime {
            let time = CMTime(seconds: startTime, preferredTimescale: 600)
            player.seek(to: time) { _ in
                player.play()
                isPlaying = true
            }
        }
    }

    private func togglePlayPause() {
        guard let player = player else { return }

        if isPlaying {
            player.pause()
        } else {
            player.play()
        }
        isPlaying.toggle()
    }

    private func seekToTime(_ seconds: Double) {
        let time = CMTime(seconds: seconds, preferredTimescale: 600)
        player?.seek(to: time)
    }

    private func seekRelative(_ seconds: Double) {
        let newTime = min(max(currentTime + seconds, 0), duration)
        seekToTime(newTime)
    }

    private func formatTime(_ seconds: Double) -> String {
        let minutes = Int(seconds) / 60
        let secs = Int(seconds) % 60
        return String(format: "%02d:%02d", minutes, secs)
    }
}

// MARK: - Preview

#Preview("Video Player") {
    VideoPlayerView(
        videoURL: URL(string: "https://example.com/video.mp4")!,
        startTime: 205.0
    )
}

#Preview("Audio Player") {
    AudioPlayerView(
        audioURL: URL(string: "https://example.com/audio.mp3")!,
        startTime: 120.0
    )
}
