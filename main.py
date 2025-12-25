# x Tools - Advanced Telegram Post/Channel Cloner
# Full support: Public & Private (Source + Target)
# Persistent config, colorful menu, real-time setup

import asyncio
import os
import json
import re
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, ChannelInvalidError
from telethon.tl.functions.channels import JoinChannelRequest

# Config & Session
CONFIG_FILE = 'xtools_config.json'
SESSION_NAME = 'xtools_session'

# Load/Save Config
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {'api_id': None, 'api_hash': None, 'phone': None, 'default_target': None}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

config = load_config()

# Colors
def green(text): return f"\033[92m{text}\033[0m"
def yellow(text): return f"\033[93m{text}\033[0m"
def blue(text): return f"\033[94m{text}\033[0m"
def red(text): return f"\033[91m{text}\033[0m"
def bold(text): return f"\033[1m{text}\033[0m"

# Header
HEADER = green("""
██╗  ██╗    ████████╗ ██████╗  ██████╗ ██╗     ███████╗
╚██╗██╔╝    ╚══██╔══╝██╔═══██╗██╔═══██╗██║     ██╔════╝
 ╚███╔╝        ██║   ██║   ██║██║   ██║██║     ███████╗
 ██╔██╗        ██║   ██║   ██║██║   ██║██║     ╚════██║
██╔╝ ██╗       ██║   ╚██████╔╝╚██████╔╝███████╗███████║
╚═╝  ╚═╝       ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝╚══════╝
                                                       
                  Advanced Channel Cloner
            Public & Private * Full Control * Persistent Setup
                        Version 2.0 Final
""")

# Parse post links
def parse_post_link(link):
    link = link.strip()
    private = re.match(r'https://t.me/c/(\d+)/(\d+)', link)
    if private:
        return int('-100' + private.group(1)), int(private.group(2)), True
    public = re.match(r'https://t.me/([a-zA-Z0-9_]+)/(\d+)', link)
    if public:
        return public.group(1), int(public.group(2)), False
    raise ValueError("Invalid post link")

# Parse any channel input
def parse_channel_input(inp):
    inp = inp.strip()
    if inp.startswith('-100') and inp[4:].isdigit():
        return int(inp), True
    if inp.isdigit():
        return int('-100' + inp), True
    if inp.startswith('https://t.me/c/'):
        code = re.match(r'https://t.me/c/(\d+)', inp)
        if code: return int('-100' + code.group(1)), True
    if inp.startswith('https://t.me/'):
        username = re.match(r'https://t.me/([a-zA-Z0-9_]+)', inp)
        if username: return username.group(1), False
    if inp.startswith('@'):
        return inp[1:], False
    return inp, False

# Parse invite
def parse_invite(link):
    if re.match(r'https://t.me/\+[A-Za-z0-9_-]+', link) or 'joinchat' in link:
        return link
    raise ValueError("Invalid invite link")

# Clone message
async def clone_message(client, msg, target):
    if msg.media:
        print(yellow("   ↓ Downloading media..."))
        path = await msg.download_media()
        print(yellow("   ↑ Uploading to target..."))
        await client.send_file(target, path, caption=msg.message or "")
        if os.path.exists(path): os.remove(path)
    else:
        await client.send_message(target, msg.message or "")

# Join if needed
async def join_if_needed(client, channel_input, is_private):
    try:
        return await client.get_entity(channel_input)
    except:
        print(red("[-] Not joined to this channel."))
        invite = input(blue("   → Enter invite link: ")).strip()
        if not invite:
            raise ValueError("No invite link")
        entity = await client.get_entity(parse_invite(invite))
        await client(JoinChannelRequest(entity))
        print(green("[+] Joined successfully!"))
        return await client.get_entity(entity.id if is_private else channel_input)

# Setup menu
async def setup_menu(client):
    while True:
        print(blue("\nSetup Menu:"))
        print(f"1. API ID       : {config['api_id'] or '(not set)'}")
        print(f"2. API Hash     : {config['api_hash'][:10] + '...' if config['api_hash'] else '(not set)'}")
        print(f"3. Phone        : {config['phone'] or '(not set)'}")
        print(f"4. Default Target: {config['default_target'] or '(not set)'}")
        print("0. Back to Main")
        ch = input(blue("Choose: ")).strip()
        if ch == '0': break
        elif ch == '1': config['api_id'] = int(input(blue("API ID: ")).strip())
        elif ch == '2': config['api_hash'] = input(blue("API Hash: ")).strip()
        elif ch == '3': config['phone'] = input(blue("Phone (+countrycode): ")).strip()
        elif ch == '4': config['default_target'] = input(blue("Default Target (link/username/ID/code): ")).strip()
        if ch in '1234':
            save_config(config)
            print(green("Saved!"))
            if ch in '123':
                print(yellow("Credentials changed → re-login required next run."))

async def main():
    if not all(config.get(k) for k in ['api_id', 'api_hash', 'phone']):
        print(red("First-time setup required!"))
        config['api_id'] = int(input(blue("Enter API ID: ")).strip())
        config['api_hash'] = input(blue("Enter API Hash: ")).strip()
        config['phone'] = input(blue("Enter Phone (+countrycode): ")).strip()
        save_config(config)

    client = TelegramClient(SESSION_NAME, config['api_id'], config['api_hash'])

    print(HEADER)
    print(blue("Connecting to Telegram..."))
    await client.start(phone=config['phone'])
    if not await client.is_user_authorized():
        await client.send_code_request(config['phone'])
        code = input(blue("Enter code: "))
        try:
            await client.sign_in(config['phone'], code)
        except SessionPasswordNeededError:
            pwd = input(blue("2FA Password: "))
            await client.sign_in(password=pwd)
    me = await client.get_me()
    print(green(f"Signed in as {bold(me.first_name)} (@{me.username or 'no username'})"))

    # Target channel
    target_input = config['default_target'] or input(blue("\nTarget Channel (link/username/ID/code): ")).strip()
    target_id, target_private = parse_channel_input(target_input)
    target_entity = await join_if_needed(client, target_id, target_private)
    print(green("[+] Target channel ready!"))

    while True:
        print(blue("\n" + "="*50))
        print(blue("                   MAIN MENU"))
        print(blue("="*50))
        print("1. Clone Single Post")
        print("2. Clone Multiple Posts")
        print("3. Clone Entire Channel")
        print("4. Setup / Change Settings")
        print("0. Exit")
        choice = input(blue("\nSelect option: ")).strip()

        if choice == '0':
            print(green("Goodbye! x Tools session ended."))
            break

        elif choice == '4':
            await setup_menu(client)
            continue

        elif choice in ['1', '2']:
            links = []
            if choice == '1':
                link = input(blue("Enter post link: ")).strip()
                if link: links = [link]
            else:
                print(blue("Enter post links (one per line, empty to finish):"))
                while True:
                    l = input().strip()
                    if not l: break
                    links.append(l)

            for link in links:
                try:
                    ch_input, post_id, private = parse_post_link(link)
                    print(yellow(f"\nProcessing: {link}"))
                    src_entity = await join_if_needed(client, ch_input, private)
                    msg = await client.get_messages(src_entity, ids=post_id)
                    if not msg:
                        print(red("[-] Post not found or deleted."))
                        continue
                    await clone_message(client, msg, target_entity)
                    print(green(f"[+] Post {post_id} cloned successfully!"))
                except Exception as e:
                    print(red(f"[-] Failed: {e}"))

        elif choice == '3':
            src_input = input(blue("Source Channel (link/username/ID/code): ")).strip()
            src_id, src_private = parse_channel_input(src_input)
            src_entity = await join_if_needed(client, src_id, src_private)

            direction = input(blue("Clone from (newest/oldest): ")).strip().lower()
            reverse = direction.startswith('n')
            confirm = input(blue("Clone ALL posts in this channel? (y/n): ")).lower()
            if confirm != 'y': continue

            print(yellow("Starting full clone... (this may take time)"))
            count = 0
            async for msg in client.iter_messages(src_entity, limit=None, reverse=reverse):
                try:
                    await clone_message(client, msg, target_entity)
                    count += 1
                    print(green(f"[+] Cloned [{count}] → Message ID: {msg.id}"))
                except Exception as e:
                    print(red(f"[-] Error on {msg.id}: {e}"))
            print(green(f"\nFull channel clone completed! Total: {count} posts."))

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
