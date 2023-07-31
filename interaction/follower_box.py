import discord
import asyncio

intents = discord.Intents.default()
intents.message_content = True

class FollowerBox(discord.ui.Select):
    
    def __init__(self, dbcon):
        self.dbcon = dbcon
        options = [discord.SelectOption(label=item.get('bot_name')) for item in dbcon.get_bot_list()]
        super().__init__(placeholder="Choose a Bot", options=options, min_values=1, max_values=1)
        
    async def callback(self, interaction: discord.Interaction):
        follower_id = interaction.user.id
        follower_info = self.dbcon.get_player_follower_and_api(follower_id)
        embed_message = "Created"
        if follower_info:
            self.dbcon.update_player_follower(self.values[0].upper(), follower_id)
            embed_message = "Updated"
        else:
            self.dbcon.add_player_follower(self.values[0].upper(), follower_id)
        
        embed = discord.Embed(
            title="ZRR Tapbit Bots",
            description=f"Bot selection {embed_message}: **{self.values[0].upper()}**",
            color=discord.Color.from_rgb(213, 86, 145)
        )
        await interaction.response.send_message(embed=embed ,ephemeral=True)
        await asyncio.sleep(10)
        await interaction.delete_original_response()
