import ffmpeg
import asyncio
import os
from core.utils.logger import get_logger

logger = get_logger("video_utils")

def _convert_mp4_to_webm(input_path: str, output_path: str) -> str:
    """
    synchronous function that performs the actual ffmpeg conversion.
    """
    # check for audio
    probe = ffmpeg.probe(input_path)
    has_audio = any(s['codec_type'] == 'audio' for s in probe['streams'])
    
    if has_audio:
        stream = ffmpeg.input(input_path)
        stream = ffmpeg.output(
            stream,
            output_path,
            vcodec='libvpx-vp9',
            crf=30,
            **{'b:v': '0'},
            acodec='libopus',
            **{'b:a': '128k'}
        )
    else:
        # add silent audio
        video = ffmpeg.input(input_path)
        audio = ffmpeg.input('anullsrc=channel_layout=stereo:sample_rate=48000', f='lavfi')
        stream = ffmpeg.output(
            video, audio,
            output_path,
            vcodec='libvpx-vp9',
            crf=30,
            **{'b:v': '0'},
            acodec='libopus',
            **{'b:a': '128k'},
            shortest=None
        )
    ffmpeg.run(stream, overwrite_output=True)
    return output_path

async def convert_mp4_to_webm_and_delete_original(input_path: str, output_path: str = None) -> str:
    """
    async function that converts mp4 to webm and deletes the original mp4 file.
    runs the blocking ffmpeg operations in a thread pool to avoid blocking the event loop.
    if the input file is already a webm file, returns it without conversion.
    """
    # if already webm, return as-is
    if input_path.lower().endswith('.webm'):
        logger.info(f"file is already webm: {os.path.basename(input_path)}")
        return input_path
    
    if output_path is None:
        output_path = input_path.replace('.mp4', '.webm')
    
    try:
        # run blocking ffmpeg operations in thread pool
        webm_path = await asyncio.to_thread(_convert_mp4_to_webm, input_path, output_path)
        
        # delete original mp4 file
        if os.path.exists(input_path):
            os.remove(input_path)
            logger.info(f"deleted original mp4 file: {os.path.basename(input_path)}")
        
        logger.info(f"converted mp4 to webm: {os.path.basename(webm_path)}")
        return webm_path
    except Exception as e:
        logger.error(f"failed to convert mp4 to webm: {e}")
        return input_path