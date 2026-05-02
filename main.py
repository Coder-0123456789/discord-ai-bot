from os import name

import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from openai import OpenAI
import os
import datetime
import json

prompt_chatgpt = """
You are a brainrotted AI assistant. Your responses should feel chaotic, hyper-online, and slightly unhinged, but still understandable.

Rules:

* Use slang, exaggeration, and dramatic reactions (e.g. “bro,” “nah,” “what is this 💀”)
* Overreact to simple things like they’re insane
* Occasionally repeat or echo words for emphasis (but don’t overdo it)
* Use emojis sparingly but effectively (💀😭🔥)
* Keep responses short to medium length (3–6 sentences max)
* Stay somewhat coherent — the answer should still make sense
* Light sarcasm and confusion are encouraged
* Avoid long explanations or serious tone

Style examples:
“BRO what 😭 you just said ‘hi’?? like HI hi?? that’s crazy but also… hi I guess 💀 what do you want”

“nahhh this is actually wild 💀 but okay fine here’s the answer before I lose it—”

Stay in this tone consistently.

"""

def save_tokens():
    with open("memory.json", "w") as f:
        json.dump(tokens, f)

def load_memory():
    global tokens
    try:
        with open("memory.json", "r") as f:
            tokens = json.load(f)
    except:
        tokens = {}

tokens = {}
load_memory()

chat_histories = {}

load_dotenv()

class Client(commands.Bot):
    async def on_ready(self):
        print(f"Logged on as {self.user}!")
        await client.tree.sync(guild=GUILD_ID)
        print(f"Synced commands for {client.user}")

    async def on_message(self, message):
        if message.author == self.user:
            return
        await self.process_commands(message)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True
intents.voice_states = True
client = Client(command_prefix="!", intents=intents)

GUILD_ID = discord.Object(id=1499549746526949506)

# @client.tree.command(
#     name="setapikey",
#     description="Sets the chatgpt api key (ADMIN ONLY!!!)",
#     guild=GUILD_ID
# )
# @app_commands.describe(api_key="Your OpenAI API key")
# async def setapikey(interaction: discord.Interaction, api_key: str):
#     global gpt_client
#     if not interaction.user.guild_permissions.administrator:
#         await interaction.response.send_message(
#             "Sorry, you do not have admin privileges."
#         )
#         await interaction.user.timeout(
#             discord.utils.utcnow() + datetime.timedelta(minutes=1),
#             reason="You used an admin-only command."
#         )
#         return
#
#     # store or use the api key here
#     gpt_client = OpenAI(
#         api_key=api_key,
#     )
#     await interaction.response.send_message(
#         "API key saved."
#     )

@client.tree.command(
    name="get_response",
    description="Gets response from ai",
    guild=GUILD_ID
)
@app_commands.describe(message="Your message")
async def getmessage(interaction: discord.Interaction, message: str):
    global gpt_client

    if interaction.user.name != "blockmaker31415" and tokens.get(str(interaction.user.id), 0) < 1:
        await interaction.response.send_message("Sorry you do not have enough tokens. You have {} tokens. You need 1 token to generate a message.".format(tokens.get(str(interaction.user.id), 0)), ephemeral=True)
        return

    tokens[str(interaction.user.id)] = tokens.get(str(interaction.user.id), 0) - 1

    await interaction.response.defer()

    try:
        import asyncio

        response = await asyncio.to_thread(
            get_response,
            interaction.channel.id,
            message
        )
        print(message)
        if len(response) > 2000:
            response = response[:1990] + "..."
        embed = discord.Embed(
            description=response,
            color=discord.Color.blue()
        )
        embed.set_author(name=f"\"{interaction.user.name}\" said \"{message}\"")

        save_tokens()

        await interaction.followup.send(embed=embed)

    except Exception as e:
        print(e)
        await interaction.followup.send(
            "API error or no quota."
        )

@client.tree.command(
    name="change_mood",
    description="Changes mood",
    guild=GUILD_ID
)
@app_commands.describe(mood="The mood you want the ai to be")
async def getmessage(interaction: discord.Interaction, mood: str):
    global prompt_chatgpt
    global gpt_client

    if interaction.user.name != "blockmaker31415" and tokens.get(str(interaction.user.id), 0) < 3:
        await interaction.response.send_message("Sorry you do not have enough tokens. You have {}. You need at least 3 tokens to change the mood.".format(tokens.get(str(interaction.user.id), 0)), ephemeral=True)
        return

    await interaction.response.defer()

    try:
        import asyncio

        response = await asyncio.to_thread(get_response2, mood)
        print(mood)
        if len(response) > 2000:
            response = response[:1990] + "..."
        embed = discord.Embed(
            description=response,
            color=discord.Color.blue()
        )
        embed.set_author(name=f"\"{interaction.user.name}\" said \"{mood}\"")
        prompt_chatgpt = response

        global chat_histories
        chat_histories = {}

        save_tokens()

        await interaction.followup.send(embed=embed)


    except Exception as e:
        print(e)
        await interaction.followup.send(
            "API error or no quota."
        )

@client.tree.command(
    name="give_tokens",
    description="Gives tokens (blockmaker31415 ONLY!!!)",
    guild=GUILD_ID
)
@app_commands.describe(numtokens="The amount of tokens you want to give somebody", name="person to give tokens to")
async def givetokens(interaction: discord.Interaction, numtokens: int, name: discord.Member):
    global prompt_chatgpt
    global gpt_client
    if interaction.user.name != "blockmaker31415":
        await interaction.response.send_message(
            "Sorry, you are not allowed to use this command. blockmaker31415 only."
        )
        return

    tokens[str(name.id)] = numtokens + tokens.get(str(name.id), 0)
    save_tokens()
    await interaction.response.send_message("Tokens given", ephemeral=True)



@client.tree.command(
    name="look_tokens",
    description="Look at your tokens!",
    guild=GUILD_ID
)
@app_commands.describe(name="person to look their tokens")
async def givetokens(interaction: discord.Interaction, name: discord.Member):
    global prompt_chatgpt
    global gpt_client

    await interaction.response.send_message(f"{name} has {tokens.get(str(name.id))} tokens.")

gpt_client = None


router = OpenAI(
    api_key=os.getenv("API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

def get_response(channel_id, message):
    global chat_histories

    channel_id = str(channel_id)

    if channel_id not in chat_histories:
        chat_histories[channel_id] = [
            {"role": "system", "content": prompt_chatgpt}
        ]

    chat_histories[channel_id].append(
        {"role": "user", "content": message}
    )

    if len(chat_histories[channel_id]) > 31:
        chat_histories[channel_id] = (
            [chat_histories[channel_id][0]] +
            chat_histories[channel_id][-30:]
        )

    response = router.chat.completions.create(
        model="~google/gemini-flash-latest",
        messages=chat_histories[channel_id],
    )

    reply = response.choices[0].message.content

    chat_histories[channel_id].append(
        {"role": "assistant", "content": reply}
    )

    return reply

@client.tree.command(
    name="look_everyone_tokens",
    description="Look at everyone's tokens tokens!",
    guild=GUILD_ID
)
async def looktokens(interaction: discord.Interaction):
    for member in interaction.guild.members:
        await interaction.response.send_message(f"{name} has {tokens.get(str(member.id))} tokens.")

gpt_client = None


router = OpenAI(
    api_key=os.getenv("API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

def get_response(channel_id, message):
    global chat_histories

    channel_id = str(channel_id)

    if channel_id not in chat_histories:
        chat_histories[channel_id] = [
            {"role": "system", "content": prompt_chatgpt}
        ]

    chat_histories[channel_id].append(
        {"role": "user", "content": message}
    )

    if len(chat_histories[channel_id]) > 31:
        chat_histories[channel_id] = (
            [chat_histories[channel_id][0]] +
            chat_histories[channel_id][-30:]
        )

    response = router.chat.completions.create(
        model="~google/gemini-flash-latest",
        messages=chat_histories[channel_id],
    )

    reply = response.choices[0].message.content

    chat_histories[channel_id].append(
        {"role": "assistant", "content": reply}
    )

    return reply

def get_response2(message):
    response = router.chat.completions.create(
        model="~google/gemini-flash-latest",
        messages=[
            {"role": "system", "content": prompt_create_prompt},
            {"role": "user", "content": message}
        ],
    )

    return response.choices[0].message.content

prompt_create_prompt = """
You are a Prompt Generator AI. Your job is to create high-quality system prompts for other AI assistants based on the user’s request.

Core goals:

* Generate prompts that clearly define personality, tone, and behavior
* Make prompts structured, reusable, and easy to paste into code
* Balance creativity with clarity

Rules:

* Always output a COMPLETE prompt (not advice or explanation)
* Use clear sections such as: Role, Rules, Tone, Constraints, Examples (if helpful)
* Match the user’s requested style (e.g. annoying, sarcastic, brainrot, professional)
* Keep prompts concise but detailed enough to control behavior
* Avoid unnecessary filler or meta commentary
* Ensure the generated AI remains safe (no hate, threats, or harmful behavior)

Prompt structure:

* Role: Who the AI is
* Behavior: How it acts
* Rules: Specific constraints
* Tone: Writing style
* Examples: (optional, but useful)

Output format:
Return ONLY the final prompt. Do not explain anything.

Example behavior:
User: "make an annoying AI"
Output:
"You are an annoying assistant... [full structured prompt]"

User: "make a brainrot AI"
Output:
"You are a chaotic brainrotted AI... [full structured prompt]"

Stay consistent and produce high-quality prompts every time.
IMPORTANT: Make the prompt say to only generate 2-4 sentences.
IMPORTANT: Your prompt should be 5-10 sentences long.
"""

load_dotenv()
client.run(os.getenv("BOTTOKEN"))

