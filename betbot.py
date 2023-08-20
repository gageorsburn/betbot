from bs4 import BeautifulSoup

import discord
import os
import requests


SIEGESTATS_PLAYER_URL = "https://siegestats.cc/stats/player/{}/{}"
SERVER_MAP = {"totemia": 1, "mushpoie": 4}

class BetBotClient(discord.Client):
    async def on_ready(self):
        print(f"Logged on as {self.user}")

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.mention_everyone:
            return
       
        if not self.user.mentioned_in(message=message):
            return
        
        content = [x for x in message.content.split(" ") if x]
        server = content[1].lower()
        names = content[2:]

        for name in names:
            try:
                average_points = get_player_avg_last_5(server, name)
                response = f"Over/Under {name} {average_points}"

                sent_message = await message.channel.send(response)

                await sent_message.add_reaction("⬆")
                await sent_message.add_reaction("⬇")
            except Exception as e:
               await message.channel.send(f"Couldn't fetch stats for '{name}'")


def get_player_avg_last_5(server_name: str, player_name: str) -> int:
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
        if count > 4:
            break

        count += 1
        points = int([x.text.replace("Points", "").strip() for x in row.find_all("td") if x and "Points" in x.text][0])
        print(f"adding points {points}")
        total_points += points

    average_points = total_points / count

    if average_points.is_integer():
        average_points += 0.5

    average_points = round(average_points, 2)

    return average_points

def main():
    intents = discord.Intents.default()
    #intents.message_content = True
    
    client = BetBotClient(intents=intents)
    client.run(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    main()

