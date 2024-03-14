import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib import font_manager
import sqlite3
import numpy as np
import io


def load_font(path):
    font_dirs = [path]
    font_files = font_manager.findSystemFonts(fontpaths=font_dirs)

    for font_file in font_files:
        font_manager.fontManager.addfont(font_file)

load_font("assets/fonts")

#font = font_manager.FontProperties(fname="assets/fonts/TW-Kai-98_1.ttf")
#print(font.get_name())
plt.rcParams["font.family"] = "DFKai-SB"
#plt.rcParams["font.family"] = font.get_name()



def _ax_make_MB(ax:plt.Axes, cursor:sqlite3.Cursor, month:str, user:int):
    """
    本月一般收支情形概況(monthly_brief)\n
    month: yyyy-mm
    """
  #select
    cursor.execute(r"SELECT SUM(amount) FROM main WHERE (item LIKE 'DI%' OR item LIKE 'II%') AND date LIKE '" + month + "%' AND user LIKE ?", (user,))
    monthly_income = round(cursor.fetchone()[0])
    cursor.execute(r"SELECT SUM(amount) FROM main WHERE (item LIKE 'DE%' OR item LIKE 'IE%') AND date LIKE '" + month + "%' AND user LIKE ?", (user,))
    monthly_expense = round(cursor.fetchone()[0])
    monthly_balance = monthly_income - monthly_expense
    expense_rate_pct = round(monthly_expense/monthly_income*100,2)
  #make
    #ms1-case1
    if monthly_balance >= 0:
        labels = [f"本月支出\n({monthly_expense}元)", f"本月結餘\n({monthly_balance}元)"]
        counts = [monthly_expense, monthly_balance]
        colors = ["gray","green"]
    #s1-case2
    elif monthly_expense <= monthly_income*2:
        labels = [f"本月超出\n({-monthly_balance}元)", f"本月收入\n({monthly_income}元)"]
        counts = [-monthly_balance, monthly_income+monthly_balance]
        colors = ["red","gray"]
    #s2
    ax.pie(counts, labels=labels, colors=colors,
            labeldistance=.3,   #顯示標籤位置
            startangle=90, counterclock=False,  #從上方開始順時針
            )
    ax.text(0, -1.25, f"本月支出率：{expense_rate_pct}%", ha="center")
    ax.set_title("本月一般收支項目")


def _ax_make_ASID(ax:plt.Axes, cursor:sqlite3.Cursor, item_list_reversed, year:str, user:int):
    """
    今年特別收支詳細(annual_special_items_detail)\n
    item_list_reversed: item code to item name\n
    year: yyyy
    """

    ax.set_xlim(0,6)  #設定子圖範圍
    #select
    cursor.execute("SELECT item, SUM(amount) FROM main WHERE item LIKE 'SE%' AND date LIKE '" + year + "%' AND user LIKE ? GROUP BY item", (user,))
    special_expenses = cursor.fetchall()
    cursor.execute("SELECT SUM(amount) FROM main WHERE item LIKE 'SI%' AND date LIKE '" + year + "%' AND user LIKE ?", (user,))
    special_income = cursor.fetchone()[0]
    total_special_expense = 0
    #chart
    labels = []
    counts = []
    for i in special_expenses:
        labels.append(item_list_reversed[i[0]][:-4] + f"\n({i[1]}元)")
        counts.append(i[1])
        total_special_expense += i[1]
    ax.pie(counts, labels=labels,
            pctdistance=.75, labeldistance=1.1,   #顯示標籤位置
            startangle=90, counterclock=False,  #從上方開始順時針
            autopct='%1.1f%%',  #自動顯示百分比
            wedgeprops={"width":0.45} #空心
            )
    ax.set_title("今年特別收支項目")
    #text
    ax.text(0,-0.15, #定位
            f"收入：{special_income}元\n支出：{total_special_expense}元\n結餘：{special_income-total_special_expense}元"
            ,ha="center") #設定對齊方式


def _ax_make_ABM(ax:plt.Axes, cursor:sqlite3.Cursor, year:str, user:int):
    """
    今年各月收支概況(annual_brief_by_month)\n
    year: yyyy
    """
    #select
    cursor.execute("SELECT substr(date, 6,2) AS month,SUM(CASE WHEN substr(item,2,1) LIKE 'E' THEN -amount ELSE amount END) FROM main WHERE (item LIKE 'D%' OR item LIKE 'I%') AND date LIKE '" + year + "%' AND user LIKE ? GROUP BY month", (user,))
    monthly_balance = cursor.fetchall()
    months = []
    values = []
    for i in monthly_balance:
        months.append(i[0].lstrip("0") + "月")
        values.append(i[1])
    #make
    bar_container = ax.bar(months,values,
                            width=0.5,)  #寬度
    ax.bar_label(bar_container, fmt='{:,.0f}')  #顯示數值
    ax.set_title("今年各月結餘")

    xmin, xmax, ymin, ymax = plt.Axes.axis(ax)  #取得現有繪圖區邊界
    ax.set(xlim=(xmin, xmax), ylim=(ymin*1.1, ymax*1.1))  #調整繪圖區邊界


def _ax_make_AEDM(ax: plt.Axes, cursor:sqlite3.Cursor, item_list_reversed, year:str, user:int):
    """
    今年各月支出詳細(annual_expense_detail_by_month)\n
    item_list_reversed: item code to item name\n
    year: yyyy
    """

    #select
    cursor.execute("SELECT substr(date, 6,2) AS month, item, SUM(amount) FROM main WHERE (item LIKE 'DE%' OR item LIKE 'IE%') AND  date LIKE '" + year + "%' AND user LIKE ? GROUP BY item,month",(user,))  #substr(column, start, step) ;"AS"是在一個要select的物件層級內
    common_expenses = cursor.fetchall()
    item_index = ""
    months = ["1月","2月","3月","4月",
                "5月","6月","7月","8月",
                "9月","10月","11月","12月",]
    
    #database -> dict
    item_expenses = {}
    for i in common_expenses:
        if i[1] != item_index:
            item_expenses[i[1]] = np.zeros(12)  #這裡用numpy只是因為我懶得打一堆零，沒特別原因
            item_index = i[1]
        item_expenses[i[1]][int(i[0])-1] = i[2]

    #dict -> figure
    bottom = np.zeros(12)
    for label,item in item_expenses.items():   #迭代dict.items()會得到k,v
        bar_container = ax.bar(months,item,width=0.5,bottom=bottom,   #堆疊的概念就是把好幾個不同的bar物件疊加起來，為了疊加就要設置一個數據條的底端起點，即bottom
                label=item_list_reversed[label])   #item_expenses的key都還是代碼
        bottom += item
    ax.bar_label(bar_container, fmt='{:,.0f}')  #顯示數值(會直接顯示最頂端的值)
    
    ax.set_title("今年各月支出詳細資料")
    ax.legend(loc="best",fontsize=8)  #設置圖例位置/字體
    
    xmin, xmax, ymin, ymax = plt.Axes.axis(ax)  #取得現有繪圖區邊界
    ax.set(xlim=(xmin, xmax), ylim=(ymin, ymax*1.1)) #調整繪圖區邊界


def _ax_make_BY(ax:plt.Axes, cursor:sqlite3.Cursor, user:int):
    """
    各年收支概述(brief_by_year)
    """
    cursor.execute("SELECT substr(date,1,4) AS year, SUM(CASE WHEN substr(item,2,1) LIKE 'E' THEN -amount ELSE amount END) FROM main WHERE user LIKE ? GROUP BY year", (user,))   #SUM(CASE...END)特別好用，語法：when...then...，其他情況則用else
    annual_balance = cursor.fetchall()

    years = []
    values = []
    for i in annual_balance:
        years.append(i[0])
        values.append(i[1])
    bar_container = ax.bar(years,values,
                            width=0.5,)  #寬度
    ax.bar_label(bar_container, fmt='{:,.0f}')  #顯示數值
    ax.set_title("歷年結餘")

    xmin, xmax, ymin, ymax = plt.Axes.axis(ax)  #取得現有繪圖區邊界
    ax.set(xlim=(xmin, xmax), ylim=(ymin*1.1, ymax*1.1))  #調整繪圖區邊界


def fig_organize_GR(date:str, cursor:sqlite3.Cursor, item_list_reversed, user:int):
    """
    通用報告圖(general_report)\n
    item_list_reversed: item code to item name\n
    date: yyyy-mm-dd\n
    回傳圖檔的BytesIO檔案
    """
    fig = plt.figure(figsize=(8,12))
    grid = GridSpec(4, 2, fig)  #網格排列
    ax1 = fig.add_subplot(grid[0, 0])
    ax2 = fig.add_subplot(grid[0, 1])
    ax3 = fig.add_subplot(grid[1, :])
    ax4 = fig.add_subplot(grid[2, :])
    ax5 = fig.add_subplot(grid[3, :])
    _ax_make_MB(ax1, cursor, date[:7], user)
    _ax_make_ASID(ax2, cursor, item_list_reversed, date[:4], user)
    _ax_make_ABM(ax3, cursor, date[:4],user)
    _ax_make_AEDM(ax4, cursor, item_list_reversed, date[:4],user)
    _ax_make_BY(ax5, cursor, user)
    fig.tight_layout()

    buffer = io.BytesIO() #建立緩衝區
    plt.savefig(buffer, format="png", dpi=100)  #將圖存入緩衝區
    buffer.seek(0)  #將指標移至緩衝區最前以利後續閱讀
    return buffer

    
