import os
import re
import subprocess

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4
from aiofiles.tempfile import TemporaryDirectory
from aiohttp import ClientSession
from tempfile import gettempdir
from aiofile import async_open

from arvid.quality import Quality, get_quality


async def get_direct_url(url: str) -> str:
    """
    Converts url to desired format.
    Raises ValueError if url is invalid
    """

    direct = r"https:\/\/v\.redd\.it\/[a-z0-9]+\/?"
    indirect = r"https:\/\/www\.reddit\.com\/(r\/[A-Za-z0-9][A-Za-z0-9_]{2,20}|user\/[A-Za-z0-9_\-]{3,20})\/comments\/[a-z0-9]+\/[^\/.]+\/?"

    if re.fullmatch(direct, url) is not None:
        return url.rstrip("/")

    if re.fullmatch(indirect, url) is None:
        raise ValueError("Wrong url format")

    jurl = url.rstrip("/") + ".json"

    async with ClientSession() as session:
        resp = await session.get(jurl)
        data = await resp.text()

    if not (m := re.findall(direct, data)):
        raise ValueError("No video attached to post")
    else:
        return m[0].rstrip("/")


async def fetch_metadata(url: str) -> tuple[list[str], list[str]]:
    """Fetches available video and audio resolutions"""
    durl = url + "/DASHPlaylist.mpd"

    async with ClientSession() as session:
        resp = await session.get(durl)
        mpd = await resp.text()

    r = r">DASH[^>]*<"

    qualities = re.findall(r, mpd)
    qualities = [q.strip("><") for q in qualities]

    audio = [q for q in qualities if "audio" in q.lower()]
    video = [q for q in qualities if "audio" not in q.lower()]

    return video, audio


async def fetch_data(
    url: str, dir: Path, video_res: str, audio_res: str | None
) -> tuple[Path, Path | None]:
    """Downloads video and audio, if set, into the dir directory"""
    async with ClientSession() as session:
        response = await session.get(url + "/" + video_res)
        async with async_open(vpath := dir / "v.mp4", "wb") as f:
            await f.write(await response.read())

        if audio_res is None:
            return vpath, None

        response = await session.get(url + "/" + audio_res)
        async with async_open(apath := dir / "a.m4a", "wb") as f:
            await f.write(await response.read())

        return vpath, apath


def combine(vpath: Path, apath: Path | None, outpath: Path) -> Path:
    """Combines video and audio into a single file"""
    if outpath.is_dir():
        outpath = outpath / f"{uuid4()}.mp4"

    cmd = (
        ["ffmpeg", "-hide_banner", "-loglevel", "panic", "-y", "-i", str(vpath)]
        + (["-i", str(apath)] if apath is not None else [])
        + ["-vcodec", "copy"]
        + (["-acodec", "copy"] if apath is not None else [])
        + [str(outpath)]
    )

    subprocess.run(cmd)

    return outpath


@dataclass
class Video:
    path: Path
    video_q: str
    audio_q: str | None


async def download(
    url: str, outpath: Path | None, video_q: Quality, audio_q: Quality
) -> Video:
    """Downloads video end returns an object, representing it. Throws ValueError if url format is incorrect"""
    url = await get_direct_url(url)

    video, audio = await fetch_metadata(url)

    video = [int(q[5 : q.find(".")]) for q in video]
    video_res = f"DASH_{get_quality(video, video_q)}.mp4"

    audio_res = None
    if audio and "audio" in audio[0]:
        audio_res = audio[0]
    elif audio:
        audio_res = f"DASH_AUDIO_{get_quality([int(q[11:q.find(".")]) for q in audio], audio_q)}.mp4"

    async with TemporaryDirectory(dir=gettempdir()) as dir:
        vpath, apath = await fetch_data(url, Path(dir), video_res, audio_res)
        outpath = combine(vpath, apath, outpath or Path(os.getcwd()))

    return Video(outpath, video_res, audio_res)
