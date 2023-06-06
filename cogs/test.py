from discord.ext import commands
import speedtest
import discord



class AdvanceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.st = speedtest.Speedtest()

    @commands.hybrid_command()
    async def test(self, ctx):
        await ctx.send("Test command executed successfully!")

    @commands.hybrid_command()
    async def ping(self, ctx):
        await ctx.send(f"Pong! Latency: {round(self.bot.latency * 1000)}ms")
    
    @commands.hybrid_command()
    async def speedtest(self, ctx):
        await ctx.defer()
        # Create an embed to show the speed test results
        embed = discord.Embed(title="Speed Test Results")

        # Ping test
        embed.add_field(name="Ping", value="Pinging servers...")
        self.st.get_best_server()
        ping_time = self.st.results.ping
        if ping_time < 70:
            embed.colour = discord.Color.green()
        elif ping_time < 150:
            embed.colour = discord.Color.orange()
        else:
            embed.colour = discord.Color.red()
        
        embed.set_field_at(index=0, name="Ping", value=f"Ping: {ping_time:.2f} ms", inline=False)
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url)

        # Download test
        embed.add_field(name="Download", value="Downloading...")
        download_speed = self.st.download() / 1000000
        embed.set_field_at(index=1, name="Download", value=f"Download speed: {download_speed:.2f} Mbps", inline=False)

        # Upload test
        embed.add_field(name="Upload", value="Uploading...")
        upload_speed = self.st.upload() / 1000000
        embed.set_field_at(index=2, name="Upload", value=f"Upload speed: {upload_speed:.2f} Mbps", inline=False)

        # Send the embed to the user
        await ctx.send(embed=embed)
async def setup(bot):
    await bot.add_cog(AdvanceCog(bot))
