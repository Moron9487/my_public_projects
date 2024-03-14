import nextcord
from nextcord.ext import commands
import sqlite3
import pytz
import datetime

if __name__ == "__main__":
    from BA_functions import make_report
else:
    from cogs.BA_functions import make_report



class DateFormatError(Exception):
    pass

def date_format_check(date:str):
    d = date.split("-")
    if len(d) != 3:
        raise DateFormatError
    if len(d[0]) != 4 or len(d[1]) != 2 or len(d[2]) != 2:
        raise DateFormatError
    try:
        d[0] = int(d[0])
        d[1] = int(d[1])
        d[2] = int(d[2])
    except ValueError:
        raise DateFormatError



class database_edit_check_box(nextcord.ui.View):
    def __init__(self,database:sqlite3.Connection,prompt:str,parameters):
        super().__init__()  #繼承nextcord.ui.View的所有屬性
        self.database = database
        self.prompt = prompt
        self.parameters = parameters
    @nextcord.ui.button(style=nextcord.ButtonStyle.red,label="確認刪除")
    async def check(self, button, interaction:nextcord.Interaction):  #button指此按鈕本身，在此三個變數都是@nextcord.ui.button這個裝飾器下的函數必備的變數
        self.database.execute(self.prompt,self.parameters)
        self.database.commit()
        await interaction.response.edit_message(content="已刪除！",view=None)
    @nextcord.ui.button(style=nextcord.ButtonStyle.gray,label="取消")
    async def cancel(self, button:nextcord.Button, interaction:nextcord.Interaction):
        await interaction.response.edit_message(content="已取消",view=None) #ephemeral message不能刪除

async def database_edit_check(warning_text:str,interaction:nextcord.Interaction,database:sqlite3.Connection,prompt:str,prompt_parameters):
    await interaction.response.send_message(content=warning_text,view=database_edit_check_box(database,prompt,prompt_parameters), ephemeral=True)


def dict_reverse(org_dict:dict):
    return {v:k for k, v in org_dict.items()}

class BotAccounter(commands.Cog):
    #D = daily; I = irregularly; S = special; A = annual
    #E = Expense; I = Income; U = uncertain;
    BA_item_list = {'三餐': 'DE-m',
                    '飲料零食': 'DE-s',
                    '交通': 'DE-t',
                    '零用錢': 'DI-p', 
                    '文具': 'IE-st',
                    '遊戲': 'IE-g', 
                    '訂閱服務': 'IE-ss',
                    '網購食物': 'IE-sn',
                    '其他非常態支出': 'IE-0',
                    '額外零用錢':'II-p',
                    '其他非常態收入':'II-0',
                    '紅包特別收入': 'SI-r',
                    '得獎特別收入':'SI-p',
                    '其他特別收入':'SI-0',
                    '科教類特別支出': 'SE-s',
                    '遊憩類特別支出': 'SE-r',
                    '動漫類特別支出': 'SE-a',
                    '電子類特別支出': 'SE-e',
                    '資訊類特別支出': 'SE-i',
                    '其他特別支出':"SE-0"
                    }
    item_list_reversed = dict_reverse(BA_item_list)
    



    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.database = sqlite3.connect("datas/BA.sql")

    @nextcord.slash_command(name="accounting")
    async def accounting(self,interaction:nextcord.Interaction):
        pass

    @accounting.subcommand(name="addentry",description="新增新的記帳項目")
    async def add_entry(self,interaction:nextcord.Interaction,
                        item:str=nextcord.SlashOption(name="item",description="記帳項目名稱",choices=BA_item_list),
                        amount:int=nextcord.SlashOption(name="amount",description="記帳項目金額"),
                        date:str=nextcord.SlashOption(name="date",description="記帳項目日期，預設為輸入當天，格式應符合yyyy-mm-dd",required=False),
                        note:str=nextcord.SlashOption(name="note",description="其他註記內容",required=False)
                        ):
        if date is None:
            date = datetime.datetime.now(tz=pytz.timezone("Asia/Taipei")).strftime(r"%Y-%m-%d")
        else:
            try:
                date_format_check(date)
            except DateFormatError:
                await interaction.response.send_message("日期格式錯誤，請使用yyyy-mm-dd格式",ephemeral=True)
                return 0
        if amount <= 0:
            await interaction.response.send_message("金額錯誤，金額應為正值",ephemeral=True)
            return 0
        cursor = self.database.cursor() 
        cursor.execute("INSERT INTO main (user,item,date,amount,note) VALUES (?,?,?,?,?)",(interaction.user.id,item,date,amount,note))
        self.database.commit()
        await interaction.response.send_message(f"已新增記帳項目如下：\nid:{cursor.lastrowid}\n記帳項目名稱：{self.item_list_reversed[item]}\n日期：{date}\n金額：{amount}\n備註：{note}",ephemeral=True)

    @accounting.subcommand(name="removeentry",description="刪除記帳項目")
    async def remove_entry(self,interaction:nextcord.Interaction,
                           entry_id:int=nextcord.SlashOption(name="id",description="欲刪除的記帳項目id")):
        cursor = self.database.cursor()
        cursor.execute("SELECT * FROM main WHERE id = ?",(entry_id,))
        entry_info = cursor.fetchone()
        if entry_info is None:
            await interaction.response.send_message("id不存在",ephemeral=True)
            return 0
        await database_edit_check(f"你欲刪除的記帳項目如下：\n記帳項目名稱：{self.item_list_reversed[entry_info[2]]}\n日期：{entry_info[3]}\n金額：{entry_info[4]}\n備註：{entry_info[5]}\n\n你確定要刪除？",
                                  interaction,
                                  self.database,
                                  "DELETE FROM main WHERE id = ?",
                                  (entry_id,))

    @accounting.subcommand(name="report",description="記帳報告")
    async def report(self, interaction:nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        date =  datetime.datetime.now(tz=pytz.timezone("Asia/Taipei")).strftime(r"%Y-%m-%d")
        report = make_report.fig_organize_GR(date, self.database.cursor(), self.item_list_reversed, interaction.user.id)
        attachment = nextcord.File(fp=report,filename="report.png")
        await interaction.followup.send(file=attachment, ephemeral=True)
        #await interaction.response.send_message(file=attachment,ephemeral=True)
    
    @accounting.subcommand(name="record",description="回傳最近十則記帳紀錄")
    async def record(self,interaction:nextcord.Interaction):
        cursor = self.database.cursor()
        cursor.execute("SELECT * FROM main ORDER BY id DESC LIMIT 10")  #DESC配合ORDER BY以達成降序排列
        embed = nextcord.Embed(title="最近記帳紀錄")
        for i in cursor.fetchall():
            embed.add_field(name="[" + str(i[0]) + "] " + self.item_list_reversed[i[2]],value=i[3] + ": " + str(i[4]) + "元", inline=False)
        await interaction.response.send_message(embed=embed,ephemeral=True)



        



def setup(bot:commands.Bot):
    bot.add_cog(BotAccounter(bot))
