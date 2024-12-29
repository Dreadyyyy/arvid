import os

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4
from aiofiles.tempfile import TemporaryDirectory
from aiohttp import ClientSession

from tempfile import tempdir

if tempdir is None:
    exit("Failed to get tempdir")

from src.quality import Quality, get_quality


def parse_url(url: str) -> str:
    """Converts url to desired format. Throws ValueError if url format is incorrect"""
    # TODO


async def fetch_metadata(url: str) -> tuple[list[int], list[int]]:
    """Fetches available video and audio resolutions"""
    async with ClientSession() as session:
        pass
    # TODO


async def fetch_data(
    url: str, dir: Path, video_res: int, audio_res: int | None
) -> tuple[Path, Path | None]:
    """Downloads video and audio, if exists, into the dir directory"""
    async with ClientSession() as session:
        pass
    # TODO


def combine(vpath: Path, apath: Path | None, outpath: Path) -> Path:
    """Combines video and audio into a single file"""
    # TODO


@dataclass
class Video:
    path: Path
    video_q: int
    audio_q: int | None


async def download(
    url: str, outpath: Path | None, video_q: Quality, audio_q: Quality
) -> Video:
    """Downloads video end returns an object, representing it. Throws ValueError if url format is incorrect"""
    url = parse_url(url)

    video, audio = await fetch_metadata(url)
    video_res = get_quality(video, video_q)
    audio_res = get_quality(audio, audio_q) if audio else None

    async with TemporaryDirectory(dir=tempdir) as dir:
        vpath, apath = await fetch_data(url, Path(dir), video_res, audio_res)
        outpath = combine(vpath, apath, outpath or Path(os.getcwd()) / f"{uuid4()}.mp4")

    return Video(outpath, video_res, audio_res)
