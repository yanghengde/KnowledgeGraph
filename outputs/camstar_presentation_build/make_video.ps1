$ErrorActionPreference = "Stop"

$ffmpeg = "D:\Deepseek\camstar\CamstarSemiOntology\outputs\camstar_presentation_build\pydeps\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
$build = "D:\Deepseek\camstar\CamstarSemiOntology\outputs\camstar_presentation_build"
$subtitle = "D\:/Deepseek/camstar/CamstarSemiOntology/outputs/CamstarOntology_视频字幕.srt"
$silentVideo = Join-Path $build "CamstarOntology_visuals.mp4"
$normalizedVideo = Join-Path $build "CamstarOntology_visuals_bt709.mp4"
$finalVideo = "D:\Deepseek\camstar\CamstarSemiOntology\outputs\CamstarOntology_主要功能介绍_字幕版.mp4"
$segmentList = Join-Path $build "video_segments.txt"

$images = @(
    (Join-Path $build "deck_renders\slide-1.png"),
    (Join-Path $build "deployed_overview.png"),
    (Join-Path $build "deck_renders\slide-2.png"),
    (Join-Path $build "deployed_search_focus.png"),
    (Join-Path $build "deployed_container_detail.png"),
    (Join-Path $build "deployed_sql_assistant.png"),
    (Join-Path $build "deck_renders\slide-3.png"),
    (Join-Path $build "deployed_query_builder.png"),
    (Join-Path $build "deck_renders\slide-1.png")
)
$durations = @(8, 12, 12, 10, 13, 11, 8, 14, 7)

for ($i = 0; $i -lt $images.Count; $i++) {
    $duration = $durations[$i]
    $segment = Join-Path $build ("segment-{0}.mp4" -f $i)
    & $ffmpeg -hide_banner -loglevel error -y -loop 1 -framerate 30 -t $duration -i $images[$i] -vf "scale=1280:720:force_original_aspect_ratio=decrease:in_range=auto:out_range=tv,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=white,setsar=1,fps=30,format=yuv420p,setparams=range=tv:color_primaries=bt709:color_trc=bt709:colorspace=bt709" -an -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -r 30 -color_range tv -colorspace bt709 -color_primaries bt709 -color_trc bt709 $segment
    if ($LASTEXITCODE -ne 0) { throw "Segment $i render failed with exit code $LASTEXITCODE" }
}

& $ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i $segmentList -c copy -movflags +faststart $silentVideo
if ($LASTEXITCODE -ne 0) { throw "Visual video concat failed with exit code $LASTEXITCODE" }

& $ffmpeg -hide_banner -loglevel error -y -i $silentVideo -vf "scale=1280:720:in_range=auto:out_range=tv,format=yuv420p,setparams=range=tv:color_primaries=bt709:color_trc=bt709:colorspace=bt709,setpts=PTS-STARTPTS" -an -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -movflags +faststart $normalizedVideo
if ($LASTEXITCODE -ne 0) { throw "BT.709 normalization failed with exit code $LASTEXITCODE" }

$subtitleFilter = "setpts=PTS-STARTPTS,subtitles='$subtitle':fontsdir='C\:/Windows/Fonts':force_style='FontName=Microsoft YaHei,FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H50000000,BackColour=&H90000000,BorderStyle=3,Outline=1,Shadow=0,MarginV=34,Alignment=2'"
& $ffmpeg -hide_banner -loglevel error -y -i $normalizedVideo -vf $subtitleFilter -an -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -movflags +faststart $finalVideo
if ($LASTEXITCODE -ne 0) { throw "Subtitle render failed with exit code $LASTEXITCODE" }

Write-Output $finalVideo
