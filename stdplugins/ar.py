"""A Torrent Client Plugin Based On Aria2 for Userbot

cmds: Magnet link : .magnet magnetLink
	  Torrent file from local: .tor file_path
	  Show Downloads: .show
	  Remove All Downloads: .ariaRM
	  Resume All Downloads: .ariaResume
	  Pause All Downloads:  .ariaP

By:- @Zero_cool7870"""
import aria2p
import asyncio
import io
import os
from uniborg.util import admin_cmd


EDIT_SLEEP_TIME_OUT = 15
aria2_daemon_start_cmd = "aria2c --enable-rpc --rpc-listen-all=false --rpc-listen-port 6800  --max-connection-per-server=10 --rpc-max-request-size=1024M --seed-time=99999 --seed-ratio=100.0 --min-split-size=10M --follow-torrent=mem --split=10 --daemon=true"
aria2_is_running = False
aria2 = None


@borg.on(admin_cmd(pattern="ariastart"))
async def aria_start(event):
    process = await asyncio.create_subprocess_shell(
        aria2_daemon_start_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    global aria2
    aria2 = aria2p.API(
        aria2p.Client(
            host="http://localhost",
            port=6800,
            secret=""
        )
    )
    OUTPUT = f"**ARIA TWO C:**\n__PID:__\n`{process.pid}`\n\n**ARIA TWO STARTED**"
    await event.edit(OUTPUT)


@borg.on(admin_cmd(pattern="addmagnet"))
async def magnet_download(event):
    if event.fwd_from:
        return
    if not aria2:
        await event.edit("Please start process using `ariastart`")
        return False
    var = event.raw_text
    var = var.split(" ")
    magnet_uri = var[1]
    logger.info(magnet_uri)
    # Add Magnet URI Into Queue
    try:
        download = aria2.add_magnet(magnet_uri)
    except Exception as e:
        logger.info(str(e))
        await event.edit("Error:\n`" + str(e) + "`")
        return
    gid = download.gid
    await check_progress_for_dl(gid, event)
    await asyncio.sleep(EDIT_SLEEP_TIME_OUT)
    new_gid = await check_metadata(gid)
    await check_progress_for_dl(new_gid, event)


@borg.on(admin_cmd(pattern="addtorrent"))
async def torrent_download(event):
    if event.fwd_from:
        return
    if not aria2:
        await event.edit("Please start process using `ariastart`")
        return False
    var = event.raw_text
    var = var.split(" ")
    torrent_file_path = var[1]
    logger.info(torrent_file_path)
    # Add Torrent Into Queue
    try:
        download = aria2.add_torrent(
            torrent_file_path,
            uris=None,
            options=None,
            position=None
        )
    except:
        await event.edit("`Torrent File Not Found...`")
        return
    gid = download.gid
    await check_progress_for_dl(gid, event)


@borg.on(admin_cmd(pattern="addurl"))
async def magnet_download(event):
    if event.fwd_from:
        return
    var = event.raw_text
    var = var.split(" ")
    url = var[1]
    logger.info(url)
    uris = [url]
    # Add URL Into Queue
    try:
        download = aria2.add_uris(uris, options=None, position=None)
    except Exception as e:
        await event.edit("`Error:\n`" + str(e))
        return
    gid = download.gid
    await check_progress_for_dl(gid, event)


@borg.on(admin_cmd(pattern="ariaRM"))
async def remove_all(event):
    if event.fwd_from:
        return
    try:
        removed = aria2.remove_all(force=True)
        aria2.purge_all()
    except:
        pass
    if removed == False:  # If API returns False Try to Remove Through System Call.
        os.system("aria2p remove-all")
    await event.edit("`Removed All Downloads.`")


@borg.on(admin_cmd(pattern="ariaP"))
async def pause_all(event):
    if event.fwd_from:
        return
    # Pause ALL Currently Running Downloads.
    paused = aria2.pause_all(force=True)
    await event.edit("Output: " + str(paused))


@borg.on(admin_cmd(pattern="ariaResume"))
async def resume_all(event):
    if event.fwd_from:
        return
    resumed = aria2.resume_all()
    await event.edit("Output: " + str(resumed))


@borg.on(admin_cmd(pattern="showariastatus"))
async def show_all(event):
    if event.fwd_from:
        return
    if not aria2:
        await event.edit("Please start process using `ariastart`")
        return False
    # Show All Downloads
    downloads = aria2.get_downloads()
    msg = ""
    for download in downloads:
        msg = msg + "File: `" + str(download.name) + "`\nSpeed: " + str(download.download_speed_string()) + "\nProgress: " + str(download.progress_string(
        )) + "\nTotal Size: " + str(download.total_length_string()) + "\nStatus: " + str(download.status) + "\nETA:  " + str(download.eta_string()) + "\n\n"
    # print(msg)
    if len(msg) <= Config.MAX_MESSAGE_SIZE_LIMIT:
        await event.edit("`Current Downloads: `\n" + msg)
    else:
        with io.BytesIO(str.encode(msg)) as out_file:
            out_file.name = "ariastatus.txt"
            await borg.send_file(
                event.chat_id,
                out_file,
                force_document=True,
                allow_cache=False,
                caption="`Output is huge. Sending as a file...`"
            )
            await event.delete()


async def check_metadata(gid):
    file = aria2.get_download(gid)
    new_gid = file.followed_by_ids[0]
    logger.info("Changing GID " + gid + " to " + new_gid)
    return new_gid


async def check_progress_for_dl(gid, event):
    complete = None
    previous_message = None
    while not complete:
        file = aria2.get_download(gid)
        complete = file.is_complete
        try:
            if not file.error_message:
                msg = f"Downloading File: `{file.name}`\nSpeed: {file.download_speed_string()}\nProgress: {file.progress_string()}\nTotal Size: {file.total_length_string()}\nStatus: {file.status}\nETA: {file.eta_string()}"
                if msg != previous_message:
                    await event.edit(msg)
                    previous_message = msg
                    await asyncio.sleep(EDIT_SLEEP_TIME_OUT)
            else:
                msg = file.error_message
                await event.edit(f"`{msg}`")
                return False
        except Exception as e:
            logger.info(str(e))
            pass
    file = aria2.get_download(gid)
    complete = file.is_complete
    if complete:
        await event.edit(f"File Downloaded Successfully:`{file.name}`")
