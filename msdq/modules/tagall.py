import asyncio

from telethon import events
from telethon.errors import UserNotParticipantError
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import ChannelParticipantAdmin
from telethon.tl.types import ChannelParticipantCreator

from msdq import client, DEV_USERS
from msdq.modules.no_sql import users_db as db
from msdq.modules.no_sql.users_db import semua

spam_chats = []


@client.on(events.NewMessage(pattern="^/tagall|@all|/all ?(.*)"))
async def mentionall(event):
    chat_id = event.chat_id
    if event.is_private:
        return await event.respond("__Perintah ini dapat digunakan dalam grup dan channel!__")

    is_admin = False
    try:
        partici_ = await client(GetParticipantRequest(
            event.chat_id,
            event.sender_id
        ))
    except UserNotParticipantError:
        is_admin = False
    else:
        if (
                isinstance(
                    partici_.participant,
                    (
                            ChannelParticipantAdmin,
                            ChannelParticipantCreator
                    )
                )
        ):
            is_admin = True
    if not is_admin:
        return await event.reply("__Hanya admin yang bisa mention semua!__")

    if event.pattern_match.group(1) and event.is_reply:
        return await event.reply("__Beri aku satu argumen!__")
    elif event.pattern_match.group(1):
        mode = "text_on_cmd"
        msg = event.pattern_match.group(1)
    elif event.is_reply:
        mode = "text_on_reply"
        msg = await event.get_reply_message()
        if msg == None:
            return await event.respond(
                "__Saya tidak bisa menyebut anggota untuk pesan lama! (pesan yang dikirim sebelum saya ditambahkan ke grup)__")
    else:
        return await event.reply("__Membalas pesan atau memberi saya beberapa teks untuk menyebutkan orang lain!__")

    spam_chats.append(chat_id)
    usrnum = 0
    usrtxt = ''
    async for usr in client.iter_participants(chat_id):
        if not chat_id in spam_chats:
            break
        usrnum += 1
        usrtxt += f"👤 [{usr.first_name}](tg://user?id={usr.id})\n"
        if usrnum == 5:
            if mode == "text_on_cmd":
                txt = f"{msg}\n\n{usrtxt}"
                await client.send_message(chat_id, txt)
            elif mode == "text_on_reply":
                await msg.reply(usrtxt)
            await asyncio.sleep(2)
            usrnum = 0
            usrtxt = ''
    try:
        spam_chats.remove(chat_id)
    except:
        pass


@client.on(events.NewMessage(pattern="^/cancel$"))
async def cancel_spam(event):
    is_admin = False
    try:
        partici_ = await client(GetParticipantRequest(
            event.chat_id,
            event.sender_id
        ))
    except UserNotParticipantError:
        is_admin = False
    else:
        if (
                isinstance(
                    partici_.participant,
                    (
                            ChannelParticipantAdmin,
                            ChannelParticipantCreator
                    )
                )
        ):
            is_admin = True
    if not is_admin:
        return await event.reply("__Hanya admin yang dapat menjalankan perintah ini!__")
    if not event.chat_id in spam_chats:
        return await event.reply("__Tidak ada proses berjalan...__")
    else:
        try:
            spam_chats.remove(event.chat_id)
        except:
            pass
        return await event.respond("__Dihentikan...__")


# Fungsi untuk menangani perintah /bc
@client.on(events.NewMessage(pattern='/bc'))
async def broadcast(event):
    # Pastikan pengguna yang mengirim perintah adalah admin atau memiliki izin untuk mengirim pesan broadcast
    if event.sender_id == DEV_USERS:
        # Periksa apakah pesan ini adalah balasan (reply) ke pesan lain
        if event.is_reply:
            # Ambil pesan yang ingin di-broadcast
            reply_message = await event.get_reply_message()
            message_text = reply_message.text

            # Ambil daftar pengguna dari database
            users = db.find({})

            success_count = 0  # Hitung jumlah pesan yang berhasil dikirim
            failure_count = 0  # Hitung jumlah pesan yang gagal dikirim
            deactivated_count = 0  # Hitung jumlah pengguna yang tidak aktif
            blocked_count = 0  # Hitung jumlah pengguna yang diblokir

            for user in users:
                user_id = user["user_id"]
                try:
                    # Kirim pesan broadcast ke setiap pengguna
                    await client.send_message(user_id, message_text)
                    success_count += 1
                except Exception as e:
                    failure_count += 1
                    if "USER_DEACTIVATED" in str(e):
                        deactivated_count += 1
                        # Hapus pengguna dari database jika tidak aktif
                        db.delete_one({"user_id": user_id})
                    elif "USER_BLOCKED" in str(e):
                        blocked_count += 1
                        # Hapus pengguna dari database jika diblokir
                        db.delete_one({"user_id": user_id})

            response_message = f'Pesan broadcast selesai:\n\n' \
                               f'Total pengguna yang berhasil: {success_count}\n' \
                               f'Total pengguna yang gagal: {failure_count}\n' \
                               f'Total pengguna yang tidak aktif: {deactivated_count}\n' \
                               f'Total pengguna yang diblokir: {blocked_count}'

            await event.reply(response_message)
        else:
            await event.reply('Anda harus membalas pesan yang ingin Anda broadcast dengan perintah ini.')
    else:
        await event.reply('Anda tidak memiliki izin untuk menggunakan perintah ini.')


# Fungsi untuk menangani perintah /users
@client.on(events.NewMessage(pattern='/users'))
async def check_users(event):
    if event.sender_id == admin_user_id:
        user_count = db.count_documents({})
        await event.reply(f'Jumlah pengguna dalam database: {user_count}')
    else:
        await event.reply('Anda tidak memiliki izin untuk menggunakan perintah ini.')


__mod_name__ = "Tag all"
__help__ = """
──「 Mention all func 」──

MSDQ-ROBOT Can Be a Mention Bot for your group.

Only admins can tag all.  here is a list of commands

× /all (reply to message or add another message) To mention all members in your group, without exception.
× /cancel for canceling the mention-all.
"""
