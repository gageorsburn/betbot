import discord
import os

from datetime import datetime
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv


load_dotenv()


class BetBotClient(discord.Client):
    async def on_ready(self):
        print(f"Logged on as {self.user}")

        kern_guild: discord.Guild = self.get_guild(693348101968232459)
        print(f"{kern_guild.name} {kern_guild.id}")

        now = datetime.now()
        yesterday = now - relativedelta(days=7)

        # interesting_channels = [1105150455308374056, 1078695843315589130, 996266078378414110, 1099374187065380914, 1066372939701813289, 1105210253773123804, 1176707158012874762, 1105210423973781544, 1105154146312663244]
        interesting_channels = [1099374187065380914]

        with open(file="kern-siege-chat.log", mode="w+", encoding="utf-8") as f:
            for channel in kern_guild.channels:
                print(f"{channel.name} {channel.id}")

                if channel.id in interesting_channels:
                    # print(f"{channel.name} {channel.id}")
                    # print(f"history for {channel.name}")
                    async for message in channel.history(oldest_first=True, limit=10000, after=yesterday):
                        msg = f"{message.id} {message.created_at} {message.author.name} {message.author.display_name} {message.content} {message.attachments}\n"
                        f.write(msg)
                #     messages = [message async for message in channel.history(limit=1000)]
                #     messages = reversed(messages)
                #     for message in messages:
                #         print(f"{message.id} {message.created_at} {message.author.name} {message.author.display_name} {message.content} {message.attachments}")

        print("done")

        # async for guild in self.fetch_guilds():
        #     print(f"{guild.name} {guild.id}")

def main():
    intents = discord.Intents.default()
    # intents.members = True
    intents.message_content = True
    
    client = BetBotClient(intents=intents)
    client.run(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    main()