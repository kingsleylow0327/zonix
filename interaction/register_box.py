import discord
import asyncio
from discord import ui 
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True

class RegisterBox(ui.Modal):
    api_key = ui.TextInput(label="API KEY",
                    style=discord.TextStyle.long,
                    placeholder="",
                    default="",
                    required = True,
                    max_length=50)
    
    api_secret = ui.TextInput(label="API SECRET",
                        style=discord.TextStyle.long,
                        placeholder="",
                        default="",
                        required = True,
                        max_length=50)

    def __init__(self, dbcon):
        self.dbcon = dbcon
        super().__init__(title = "API Registration/Update")
        
    async def on_submit(self, interaction: discord.Interaction):
        follower_id = interaction.user.id
        follower_info = self.dbcon.get_player_follower_and_api(follower_id)
        embed_message = "Created"
        if not follower_info or (not follower_info.get('api_key') and not follower_info.get('api_secret')):
            self.dbcon.add_player_api(follower_id, self.api_key, self.api_secret)
        else:
            self.dbcon.update_player_api(follower_id, self.api_key, self.api_secret)
            embed_message = "Updated"
        
        embed= discord.Embed (title= self.title, description=f"*API {embed_message} with key:*\n{self.api_key}",
                              timestamp = datetime.now(),
                              color = discord.Colour.blue())
        embed.set_author(name = interaction.user, icon_url=interaction.user.avatar)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await asyncio.sleep(10)
        await interaction.delete_original_response()