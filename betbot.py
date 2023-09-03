from bs4 import BeautifulSoup
from collections import defaultdict
from dotenv import load_dotenv
from typing import NamedTuple

import cachetools
import discord
import os
import requests
import uuid


load_dotenv()


SIEGESTATS_PLAYER_URL = "https://siegestats.cc/stats/player/{}/{}"
SERVER_MAP = {"totemia": 1, "mushpoie": 4}

PREVIEW_SERVERS = [1049918229981691904, 1135323031498149929]
BAD_BP = "Cuhz"


ids_player_messages = cachetools.TTLCache(maxsize=128, ttl=60 * 60 * 24)


class PlayerServerMessage(NamedTuple):
    message_id: int
    server: str


class BetBotClient(discord.Client):
    async def on_ready(self):
        print(f"Logged on as {self.user}")

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.mention_everyone:
            return

        if BAD_BP.lower() in message.content.lower() and message.channel.guild.id in PREVIEW_SERVERS:
            await message.channel.send(f"{message.author.mention} Did you mean to say clown?")

        if not self.user.mentioned_in(message=message):
            return
        
        content = [x for x in message.content.split(" ") if x]
        server = content[1].lower()

        if server == "tally":
            bet_id = content[2]
            players_in_bet = ids_player_messages.get(bet_id, {})

            win_count, lose_count = 0, 0

            for player, player_server_message in players_in_bet.items():
                last_score = get_player_avg(player_server_message.server, player_name=player, last_index=0)
                player_message = await message.channel.fetch_message(player_server_message.message_id)
                old_avg = float(player_message.content.split(" ")[2])

                if last_score > old_avg:
                    tally_reaction = "✅"
                    win_count += 1
                else:
                    tally_reaction = "❌"
                    lose_count += 1

                await player_message.add_reaction(tally_reaction)

            await message.channel.send(f"Win Count: {win_count}\nLose Count: {lose_count}")
            return

        names = content[2:]

        bet_id = str(uuid.uuid4())

        for name in names:
            try:
                average_points = get_player_avg(server, name)

                if average_points.is_integer():
                    average_points += 0.5

                average_points = round(average_points, 2)

                response = f"Over/Under {name} {average_points}"

                sent_message = await message.channel.send(response)

                player_message_cache = ids_player_messages.setdefault(bet_id, {})
                player_message_cache[name] = PlayerServerMessage(message_id=sent_message.id, server=server)

                await sent_message.add_reaction("⬆")
                await sent_message.add_reaction("⬇")
            except Exception as e:
               print(e)
               await message.channel.send(f"Couldn't fetch stats for '{name}'")

        await sent_message.channel.send(f"Bet ID: {bet_id}")


def get_player_avg(server_name: str, player_name: str, last_index=4) -> int:
    server_id = SERVER_MAP.get(server_name, 4)
    url = SIEGESTATS_PLAYER_URL.format(server_id, player_name)
    response = requests.get(url)
    response.raise_for_status()

    html = BeautifulSoup(response.text, "html.parser")
    main_content_container = html.body.find("div", {"id": "mainContentContainer"})
    latest_appearances = main_content_container.find("div", {"id": "tableLastAppearances"})
    rows = latest_appearances.table.find_all("tr")

    count = 0
    total_points = 0

    for row in rows:
        if count > last_index:
            break

        count += 1
        points = int([x.text.replace("Points", "").strip() for x in row.find_all("td") if x and "Points" in x.text][0])
        total_points += points

    average_points = total_points / count

    return average_points

def main():
    intents = discord.Intents.default()
    intents.message_content = True
    
    client = BetBotClient(intents=intents)
    client.run(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    main()

