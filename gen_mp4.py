import os
import ffmpeg
import asyncio
import edge_tts
import toml

async def generate_tts(text, output_file):
    tts = edge_tts.Communicate(text, "zh-CN-XiaoyiNeural")
    await tts.save(output_file)
    return output_file

def generate_srt(subtitle_text, duration, srt_file):
    """ 生成 SRT 字幕文件 """
    duration = duration+0.5
    with open(srt_file, "w", encoding="utf-8") as f:
        f.write("1\n")
        f.write("00:00:00,000 --> 00:00:{:02d},000\n".format(int(duration)))
        f.write(subtitle_text + "\n")

def create_video(image, text, audio, srt_file, duration, output_file):
    """ 使用 ffmpeg 生成 1080p MP4 视频，带 SRT 字幕 """
    
    
    
    # 适配 1080p
    video = ffmpeg.input(image, loop=1, t=duration)
    video = video.filter("scale", 1920, 1080).filter("format", "yuv420p")
    
    input_audio = ffmpeg.input(audio)
    
    # 添加 SRT 字幕
    video = video.filter("subtitles", srt_file)
    
    # 合成视频
    ffmpeg.output(video, input_audio, output_file, vcodec='libx264', acodec='aac', strict='experimental').run(overwrite_output=True)
    
    # 清理临时字幕文件
    #os.remove(srt_file)
    print(f"视频已生成: {output_file}")


def generate_video_from_toml(config_path):
    # 解析 TOML 配置
    with open(config_path, 'r', encoding='utf-8') as f:
        config = toml.load(f)

    output_video = config.get("mp4", "output.mp4")
    items = config.get("item", [])

    if not items:
        print("错误: 没有找到任何帧信息!")
        return

    tindex = 0
    ofiles = []
    for item in items:
        tmp_v = f"temp/o_{tindex}.mp4"
        audio = f"temp/tts_{tindex}.mp3"
        srt_file = f"temp/srt_{tindex}.srt"

        tindex += 1
        image_file = item["file"]
        duration = float(item["duration"].strip("s"))
        text = item.get("txt", "")

        if not os.path.exists(image_file):
            print(f"错误: 图片 {image_file} 不存在，跳过！")
            continue

        auido = asyncio.run(generate_tts(text, audio))

        # 获取音频时长
        probe = ffmpeg.probe(audio)
        duration = float(probe["format"]["duration"]) + 1.0

        # 生成字幕文件
        generate_srt(text, duration, srt_file)

        create_video(image_file, text, audio, srt_file, duration, tmp_v)
        #gen_one(image_file, text, tmp_v)
        ofiles.append(tmp_v)

    print(ofiles)
    merge_videos(ofiles, output_video)
    print("mp4: {output_file}")

def merge_videos(mp4_list, output_file):
   # 创建临时文件 list.txt
    list_file = "temp/filelist.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for mp4 in mp4_list:
            mp4 = os.path.basename(mp4)
            f.write(f"file '{mp4}'\n")

    # 调用 ffmpeg 合并视频
    ffmpeg.input(list_file, format="concat", safe=0).output(output_file, c="copy").run(overwrite_output=True) 

# 运行示例
if __name__ == "__main__":
    generate_video_from_toml("config.toml")

