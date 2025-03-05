import toml
import ffmpeg
import os

def generate_video_from_toml(config_path):
    # 解析 TOML 配置
    with open(config_path, 'r', encoding='utf-8') as f:
        config = toml.load(f)

    output_video = config.get("mp4", "output.mp4")
    items = config.get("item", [])

    if not items:
        print("错误: 没有找到任何帧信息!")
        return

    # 生成文件列表 fl.txt 和字幕文件 s.srt
    file_list_path = "fl.txt"
    subtitle_path = "s.srt"

    with open(file_list_path, "w", encoding="utf-8") as fl, open(subtitle_path, "w", encoding="utf-8") as srt:
        subtitle_index = 1
        time_offset = 0.0  # 时间偏移

        for item in items:
            image_file = item["file"]
            duration = float(item["duration"].strip("s"))
            text = item.get("txt", "")

            if not os.path.exists(image_file):
                print(f"错误: 图片 {image_file} 不存在，跳过！")
                continue

            # 追加到文件列表
            fl.write(f"file '{image_file}'\nduration {duration}\n")

            # 追加到字幕文件 (SRT 格式)
            start_time = time_offset
            end_time = time_offset + duration
            srt.write(f"{subtitle_index}\n")
            srt.write(f"{format_time(start_time)} --> {format_time(end_time)}\n")
            srt.write(f"{text}\n\n")

            subtitle_index += 1
            time_offset = end_time

    # 处理 FFmpeg
    input_stream = ffmpeg.input(file_list_path, format="concat", safe=0)
    input_stream = input_stream.filter("subtitles", subtitle_path)

    output_stream = ffmpeg.output(input_stream, output_video, vcodec="libx264", pix_fmt="yuv420p")
    
    # 执行 FFmpeg
    ffmpeg.run(output_stream, overwrite_output=True)
    print(f"视频已生成: {output_video}")

def format_time(seconds):
    """格式化时间为 SRT 标准 (hh:mm:ss,ms)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

# 运行示例
generate_video_from_toml("config.toml")

