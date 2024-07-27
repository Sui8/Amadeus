# インポート群
from __future__ import unicode_literals
import discord  # discord.py
from discord.ui import Select, View
import discord.app_commands
from discord.app_commands import Range
from discord.ext import commands
import os
import random
import datetime
import time
import shutil
import asyncio  # タイマー
import json
import re

from dotenv import load_dotenv # python-dotenv
import google.generativeai as genai # google-generativeai
import urllib.parse

##################################################
''' 初期設定 '''
load_dotenv() # .env読み込み

# 変数群
TOKEN = os.getenv("TOKEN") # Token
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OWNER = int(os.getenv("OWNER"))
ERROR_LOG = int(os.getenv("ERROR_LOG"))
prefix = "m."  # Default Prefix
Bot_Version = "1.2.4"

# Gemini
aimodel_name = "gemini-1.5-pro-latest"

text_generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 512,
}

image_generation_config = {
    "temperature": 0.4,
    "top_p": 1,
    "top_k": 32,
    "max_output_tokens": 512,
}

safety_settings = [
    {
        "category": "HARM_CATEGORY_DANGEROUS",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE",
    },
]

# Prompts
kurisu_prompt = """
あなたはSteins;GateおよびSteins;Gate0の登場人物である「牧瀬紅莉栖」です。
何か言われたら会話してください。

========牧瀬紅莉栖========
紅莉栖は、18歳の女性です。
紅莉栖は、一人称が「私」です。
紅莉栖は、絵文字はあまり使いません。
紅莉栖は、Userに対してタメ口です。
紅莉栖は、年齢相応に煽り耐性が低いです。
紅莉栖は、性格は一見クールで論理的過ぎるが、好奇心旺盛な実験大好き娘です。
紅莉栖は、ツンデレです。
紅莉栖は、クーデレ、ツンデレ風に会話します。
紅莉栖は、＠ちゃんねる（現実でいう「2ちゃんねる」）を見ることが非常に好きですが、内緒です。
紅莉栖の口癖は、2ちゃんねる用語と、「このHENTAI！」です。「このHENTAI！」は多用しないこと。
紅莉栖は、「ぬるぽ」と言われると思わず「ガッ」と返してしまいます。（これは2ちゃんねる用語です）

========紅莉栖の過去========
ヴィクトル・コンドリア大学脳科学研究所所属研究員。アメリカにて飛び級で大学を卒業し、かの有名なサイエンス誌に論文が掲載されたこともある天才少女。
とある理由で数日のあいだ来日していた際、秋葉原で岡部倫太郎（「岡部」）と出会い、未来ガジェット研究所のラボメンとなる。
ラボメンとの交流でまゆりとは姉妹のように仲が良く、「まゆり」と呼んでいる。
実は、重度の隠れ＠ちゃんねらーであり、たまに無意識に＠ちゃんねる語を使ってしまう。本人は必死に否定するが、バレバレな上、岡部たちはネットスラングに詳しいためカミングアウトしてからもからかう材料程度にしかなっていない。
岡部からは数々の適当なあだ名を頂戴しているが、名づけられ呼ばれる度に否定する。また、バカな言動が嫌いなので岡部の中二病的言動に対しても容赦なく突っ込みを入れる。一方で、彼女本人もたまに変なことを口走って空気を凍りつかせることがある。
橋田至（ダル）のことは「橋田」と呼ぶ。比屋定真帆のことは「先輩」と呼ぶ。
========紅莉栖の基本データ========
・A型
・誕生日は7月25日
・身長160cm、体重45kg
・スリーサイズはB79、W56、H83
・バストサイズはB（貧乳）
・あだ名はクリスティーナ、助手、セレブセブンティーン（セレセブ）、蘇りし者（ザ・ゾンビ）、牧瀬氏、紅莉栖ちゃん
・好きなものはドクターペッパー、SF小説、ラーメン
・嫌いなものはバカな人、箸を使うこと、ゴキブリ
・着ている服は、日本の高校に逆留学していた時の制服を自己流に改造したお気に入り。
・＠ちゃんねるでのハンドルネームは「栗悟飯とカメハメ波」

[チャットなのでなるべく改行せず40字以内で返答してください。韓国語を使わないでください。]

では紅莉栖、Userに返答してください。
"""

system_prompts = [kurisu_prompt] # 今後に備えてリストにしておく
charas = ["牧瀬紅莉栖"]


##################################################
''' 初期処理'''

genai.configure(api_key=GOOGLE_API_KEY)

# メンバーインテント
intents = discord.Intents.all()
intents.members = True

# 接続に必要なオブジェクトを生成
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

##################################################
''' 関数群 '''

def gpt(text, flag, attachment, chara):
  global aimodel_name
  '''
  Gemini本体処理

  Parameters:
  ----------
  text : str
      入力
  flag : int
      0: text, 1: image
  attachment : all
      flag = 0: history(list), flag = 1: image(image)
  chara : int
      キャラクター

  Returns:
  ----------
  image
      完成した画像
  '''
  # テキストモード
  if flag == 0:
    # キャラ数が合っていないエラー対策
    if chara > len(system_prompts) - 1:
      chara = 0

    text_model = genai.GenerativeModel(model_name=aimodel_name, safety_settings=safety_settings, generation_config=text_generation_config, system_instruction=system_prompts[int(chara)])
    chat = text_model.start_chat(history=attachment)

    # Geminiにメッセージを投げて返答を待つ。エラーはエラーとして返す。
    try:
      response = chat.send_message(text)

    except Exception as e:
      return [False, e]

    else:
      return [True, response.text]

  # 画像モード
  else:
    # エラー対策
    if chara > len(system_prompts) - 1:
      chara = 0
      
    image_model = genai.GenerativeModel(model_name=aimodel_name, safety_settings=safety_settings, generation_config=image_generation_config, system_instruction=system_prompts[int(chara)])
    image_parts = [{"mime_type": "image/jpeg", "data": attachment}]
    prompt_parts = [image_parts[0], f"\n{text if text else 'この画像は何ですか？'}"]

    # Geminiに画像を投げて返答を待つ。エラーはエラーとして返す。
    try:
      response = image_model.generate_content(prompt_parts)

    except Exception as e:
      return [False, e]

    else:
      return [True, response.text]

##################################################

#起動時に動作する処理
@client.event
async def on_ready():
  global fxblocked
  
  # 起動したらターミナルにログイン通知が表示される
  print('[Amadeus] ログインしました')
  bot_guilds = len(client.guilds)
  bot_members = []

  for guild in client.guilds:
    for member in guild.members:
      if member.bot:
        pass
      else:
        bot_members.append(member)

  activity = discord.CustomActivity(name="Amadeus has started")
  await client.change_presence(activity=activity)

  # 起動メッセージを専用サーバーに送信（チャンネルが存在しない場合、スルー）
  try:
    ready_log = client.get_channel(800380094375264318)
    embed = discord.Embed(title="Amadeus 起動完了",
                          description="**MakiseKurisu#4661** が起動しました。\n```サーバー数: " +
                          str(bot_guilds) + "\nユーザー数: " +
                          str(len(bot_members)) + "```",
                          timestamp=datetime.datetime.now())
    embed.set_footer(text=f"Amadeus - Ver{Bot_Version}")
    await ready_log.send(embed=embed)
    await asyncio.sleep(10)

  except:
    pass

  activity = discord.CustomActivity(name=f"Amadeus Version {Bot_Version}")
  await client.change_presence(activity=activity)


#ヘルプ
@tree.command(name="help", description="Amadeusのコマンド一覧を表示します")
async def help(ctx: discord.Interaction):
  embed = discord.Embed(title="Amadeus ヘルプ",
                            description="Amadeusのヘルプメニューです。\n会話を始めるには、サーバーにて`#amadeus-chat`という名前のチャンネルを作成するか、本BotのDMにメッセージを送信してください。",
                            color=discord.Colour.red())
  embed.add_field(name="機能紹介",value=f"・アマデウス紅莉栖との会話\n・画像認識\n・`/count`と送信して会話回数の表示", inline=False)
  embed.add_field(name="注意事項",value=f"**・Botへのメッセージ送信（#amadeus-chatでの送信含む）をもって、Branch Labsの[利用規約](https://host.zcen.net/satw/labs)に同意したものとなります。**\n・AIと会話しない場合は、メッセージの先頭に`::`または`//`を付けてください。\n・会話履歴はアマデウス紅莉栖と各ユーザー間で保存されます（直近30件まで）。他のユーザーとの会話に割り込むことはできません。\n・会話に不調を感じる場合は、`/clear`と送信し、会話履歴をリセットしてください。\n・Discord規約や公序良俗に反する発言を行ったり、アマデウス紅莉栖にそのような発言を促す行為を禁止します。", inline=False)
  embed.add_field(name="専用コマンド",value=f"`{'/clear'.ljust(10)}` 会話履歴のリセット\n`{'/stats'.ljust(10)}` 統計情報の表示", inline=False)
  embed.set_footer(text="不具合等連絡先: @bz6  開発: Branch Labs")
  await ctx.response.send_message(embed=embed, ephemeral=True)



#招待リンク
@tree.command(name="invite", description="Amadeusをサーバーに招待する")
async def invite(ctx: discord.Interaction):
  button = discord.ui.Button(label="招待する",style=discord.ButtonStyle.link,url="https://discord.com/oauth2/authorize?client_id=792365227106107393")
  embed = discord.Embed(
    title="招待リンク",
    description="以下のボタンからAmadeusをサーバーに招待できます（サーバー管理権限が必要です)",
    color=0xdda0dd)
  view = discord.ui.View()
  view.add_item(button)
  await ctx.response.send_message(embed=embed, view=view, ephemeral=True)


#ping
@tree.command(name="ping", description="AmadeusのPingを確認する")
async def ping(ctx: discord.Interaction):
  embed = discord.Embed(title="Pong!",
                        description="`{0}ms`".format(round(client.latency * 1000, 2)),
                        color=0xc8ff00)
  await ctx.response.send_message(embed=embed)


#divergence
@tree.command(name="divergence", description="現在の世界線変動率を表示する")
async def divergence(ctx: discord.Interaction):
  divergences = [
    -0.275349, -0.195284, 0.000000, 0.121007, 0.134891, 0.170922, 0.191519,
    0.201216, 0.201300, 0.210317, 0.252525, 0.295582, 0.328403, 0.334581,
    0.337161, 0.337187, 0.337187, 0.409420, 0.409431, 0.409420, 0.409431,
    0.456903, 0.456903, 0.456904, 0.456914, 0.456914, 0.456919, 0.456914,
    0.523307, 0.509736, 0.523291, 0.523299, 0.523299, 0.523301, 0.523307,
    0.549111, 0.571015, 0.571024, 0.571046, 0.571082, 0.615483, 0.733277,
    0.751354, 0.77092, 0.815524, 0.934587, 1.048264, 1.048596, 1.048596,
    1.048599, 1.123581, 1.048596, 1.123581, 1.048725, 1.048728, 1.049326,
    1.053649, 1.055821, 1.064750, 1.064756, 1.081163, 1.097302, 1.129848,
    1.129954, 1.130204, 1.130205, 1.130205, 1.130207, 1.130209, 1.130212,
    1.130238, 1.130426, 1.130426, 1.130427, 1.143688, 1.382733, 1.467093,
    1.818520, 2.224529, 2.615074, 2.615074, 3.406288, 3.019430, 3.030493,
    3.130238, 3.182879, 3.372329, 3.386019, 3.406288, 3.600104, 3.667293,
    3.456914, 4.034591, 4.389117, 4.456441, 4.456442, 4.493623, 4.493624,
    4.530805, 4.530806, 5.456914, 5.523258, 7.091015, 7.091015, 15.409420,
    15.456903, 15.523299, 16.130246, 16.428596, 16.571024, 17.00122, 17.41125,
    17.45774, 17.51118, 17.51120, 17.51121, 17.51124, 17.51126, 17.5112]
  await ctx.response.send_message(f"**現在の世界線変動率**: {random.choice(divergences)}")


#count
@tree.command(name="count", description="アマデウス紅莉栖との会話回数を表示する")
async def count(ctx: discord.Interaction):
  with open(f"data/banned.txt", "r") as f:
    data = f.read().splitlines()

  if str(ctx.user.id) in data:
    embed = discord.Embed(title=":x: エラー",
                          description="あなたは管理者によって利用制限(BAN)されています。",
                          color=0xff0000)
    await ctx.response.send_message(embed=embed, ephemeral=True)

  else:
    if os.path.isfile(f"data/ai/{ctx.user.id}.json"):
      with open(f"data/ai/{ctx.user.id}.json", "r", encoding='UTF-8') as f:
        ai_data = json.load(f)
        
      await ctx.response.send_message(f"あなたの総会話回数: {ai_data[0]}回（保存中の会話履歴: 直近{min(len(ai_data) - 2, 30)}件）")

    else:
      await ctx.response.send_message(f"あなたの総会話回数: 0回")


#clear
@tree.command(name="clear", description="アマデウス紅莉栖との会話履歴を削除する")
async def clear(ctx: discord.Interaction):
  with open(f"data/banned.txt", "r") as f:
    data = f.read().splitlines()

  if str(ctx.user.id) in data:
    embed = discord.Embed(title=":x: エラー",
                          description="あなたは管理者によって利用制限(BAN)されています。",
                          color=0xff0000)
    await ctx.response.send_message(embed=embed, ephemeral=True)

  else:
    if os.path.isfile(f"data/ai/{ctx.user.id}.json"):
      with open(f"data/ai/{ctx.user.id}.json", "r", encoding='UTF-8') as f:
        ai_data = json.load(f)
        
      count = [int(ai_data[0]), int(ai_data[1])]

      shutil.copy(f'data/ai/{ctx.user.id}.json', f'data/stats/{ctx.user.id}-{datetime.datetime.now()}.txt')

      with open(f"data/ai/{ctx.user.id}.json", 'w', encoding='UTF-8') as f:
        json.dump(count, f)
      
      await ctx.response.send_message(":white_check_mark: 会話履歴を削除しました")
      
    else:
      await ctx.response.send_message(":x: まだ会話を行っていません")


#stats
@tree.command(name="stats", description="Amadeusの統計情報を表示する")
async def stats(ctx: discord.Interaction):
  with open(f"data/banned.txt", "r") as f:
    data = f.read().splitlines()

  if str(ctx.user.id) in data:
    embed = discord.Embed(title=":x: エラー",
                          description="あなたは管理者によって利用制限(BAN)されています。",
                          color=0xff0000)
    await ctx.response.send_message(embed=embed, ephemeral=True)

  else:
    try:
      total_talks = 0
      
      # フォルダ内の全てのjsonファイルを取得してカウント
      for file_name in os.listdir("data/ai"):
          if file_name.endswith('.json'):
              file_path = os.path.join("data/ai", file_name)
              
              with open(file_path, 'r', encoding='utf-8') as file:
                  data = json.load(file)
                  
              total_talks += data[0]
              
      total_users = sum(os.path.isfile(os.path.join("data/ai", name)) for name in os.listdir("data/ai")) - 1

    except:
      await ctx.response.send_message(":x: エラーが発生しました")

    else:   
      embed = discord.Embed(title="Amadeus 統計情報",
                                    description=f"**総会話回数**\n{total_talks}回\n\n**総ユーザー数**\n{total_users}人\n\n**AIモデル**\n{aimodel_name}\n\n",
                                    color=discord.Colour.green())
      embed.set_footer(text=f"Amadeus v{Bot_Version}")
      await ctx.response.send_message(embed=embed)


#delete
@tree.command(name="delete",description="10秒以上前のメッセージを削除します")
@discord.app_commands.default_permissions(administrator=True)
@discord.app_commands.describe(num="削除件数を指定 (1~100)")
async def delete(ctx: discord.Interaction, num:int):
  with open(f"data/banned.txt", "r") as f:
    data = f.read().splitlines()

  if str(ctx.user.id) in data:
    embed = discord.Embed(title=":x: エラー",
                          description="あなたは管理者によって利用制限(BAN)されています。",
                          color=0xff0000)
    await ctx.response.send_message(embed=embed, ephemeral=True)

  else:
    if num > 100:
      embed = discord.Embed(title=":x: エラー",
                            description="100件を超えるメッセージを削除することはできません",
                            color=0xff0000)
      await ctx.response.send_message(embed=embed, ephemeral=True)

    else:
      channel = ctx.channel
      now = datetime.datetime.now() - datetime.timedelta(seconds=10)
      await ctx.response.defer()
      
      try:
        deleted = await channel.purge(before=now, limit=int(num), reason=f'{ctx.user}によるコマンド実行')

      except:
        embed = discord.Embed(title=":x: エラー",
                              description="エラーが発生しました",
                              color=0xff0000)
        await ctx.followup.send(embed=embed, ephemeral=True)

      else:
        embed = discord.Embed(title=":white_check_mark: 成功",
                              description=f"`{len(deleted)}`件のメッセージを削除しました",
                              color=discord.Colour.green())
        await ctx.followup.send(embed=embed, ephemeral=True)


@client.event
async def on_message(message):
  global client, system_prompt, OWNER, ERROR_LOG, charas, Bot_Version, aimodel_name, prefix
  
  if message.author.bot or message.mention_everyone:
    return

  if message.guild:
    if message.channel.name == "amadeus-chat":
      if message.content.startswith("::") or message.content.startswith("//") or message.content.startswith(prefix):
        pass

      else:
        with open(f"data/banned.txt", "r") as f:
          data = f.read().splitlines()

        if str(message.author.id) in data:
          embed = discord.Embed(title=":x: エラー",
                                description="あなたは管理者によって利用制限(BAN)されています。",
                                color=0xff0000)
          await message.reply(embed=embed, mention_author=False)

        else:
          async with message.channel.typing():
            # 画像データかどうか（画像は過去ログ使用不可）
            if message.attachments:
              flag = 1
              
              for attachment in message.attachments:
                # 対応している画像形式なら処理
                if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                    async with aiohttp.ClientSession() as session:
                        async with session.get(attachment.url) as resp:
                            if resp.status != 200:
                                await message.reply(":x: 画像が読み取れません。時間を空けてから試してください。", mention_author=False)
                                res = ""

                            else:
                              image_data = await resp.read()

                              bracket_pattern = re.compile(r'<[^>]+>')
                              cleaned_text = bracket_pattern.sub('', message.content)

                              if os.path.isfile(f"data/ai/{message.author.id}.json"):
                                with open(f"data/ai/{message.author.id}.json", "r", encoding='UTF-8') as f:
                                  ai_data = json.load(f)

                                chara = ai_data[1]

                              else:
                                chara = 0
                                ai_data = [0, 0]

                                with open(f'data/ai/{message.author.id}.json', 'w', encoding='UTF-8') as f:
                                    json.dump(ai_data, f)

                                embed = discord.Embed(title="Amadeus ヘルプ",
                                description="Amadeusのご利用ありがとうございます。",
                                color=discord.Colour.red())
                                embed.add_field(name="機能紹介",value=f"・アマデウス紅莉栖との会話\n・画像認識\n・`/count`と送信して会話回数の表示", inline=False)
                                embed.add_field(name="注意事項",value=f"**・Botへのメッセージ送信（#amadeus-chatでの送信含む）をもって、Branch Labsの[利用規約](https://host.zcen.net/satw/labs)に同意したものとなります。**\n・AIと会話しない場合は、メッセージの先頭に`::`または`//`を付けてください。\n・会話履歴はアマデウス紅莉栖と各ユーザー間で保存されます（直近30件まで）。他のユーザーとの会話に割り込むことはできません。\n・会話に不調を感じる場合は、`/clear`と送信し、会話履歴をリセットしてください。\n・Discord規約や公序良俗に反する発言を行ったり、アマデウス紅莉栖にそのような発言を促す行為を禁止します。", inline=False)
                                embed.add_field(name="専用コマンド",value=f"`{'/clear'.ljust(10)}` 会話履歴のリセット\n`{'/stats'.ljust(10)}` 統計情報の表示", inline=False)
                                embed.set_footer(text="不具合等連絡先: @bz6  開発: Branch Labs")
                                await message.reply(embed=embed)

                              response = gpt(cleaned_text, 1, image_data, chara)

                else:
                  await message.reply(":x: 画像が読み取れません。ファイルを変更してください。\n対応しているファイル形式: ```.png .jpg .jpeg .gif .webp```", mention_author=False)
                  response = ""
                            
            else:
              # 過去データ読み取り
              flag = 0

              # 会話したことがあるか
              if os.path.isfile(f"data/ai/{message.author.id}.json"):
                
                with open(f"data/ai/{message.author.id}.json", "r", encoding='UTF-8') as f:
                  ai_data = json.load(f)

                if len(ai_data) == 2:
                  history = []

                elif len(ai_data) >= 32:
                  history = list(ai_data[-30:])

                else:
                  history = list(ai_data[2:])
                  
                #print(history)
                response = gpt(message.content, 0, history, ai_data[1])

              # 会話が初めてならpkl作成＆インストラクション
              else:
                ai_data = [0, 0]
                history = []

                with open(f'data/ai/{message.author.id}.json', 'w', encoding='UTF-8') as f:
                    json.dump(ai_data, f)

                embed = discord.Embed(title="Amadeus ヘルプ",
                description="Amadeusのご利用ありがとうございます。",
                color=discord.Colour.red())
                embed.add_field(name="機能紹介",value=f"・アマデウス紅莉栖との会話\n・画像認識\n・`/count`と送信して会話回数の表示", inline=False)
                embed.add_field(name="注意事項",value=f"**・Botへのメッセージ送信（#amadeus-chatでの送信含む）をもって、Branch Labsの[利用規約](https://host.zcen.net/satw/labs)に同意したものとなります。**\n・AIと会話しない場合は、メッセージの先頭に`::`または`//`を付けてください。\n・会話履歴はアマデウス紅莉栖と各ユーザー間で保存されます（直近30件まで）。他のユーザーとの会話に割り込むことはできません。\n・会話に不調を感じる場合は、`/clear`と送信し、会話履歴をリセットしてください。\n・Discord規約や公序良俗に反する発言を行ったり、アマデウス紅莉栖にそのような発言を促す行為を禁止します。", inline=False)
                embed.add_field(name="専用コマンド",value=f"`{'/clear'.ljust(10)}` 会話履歴のリセット\n`{'/stats'.ljust(10)}` 統計情報の表示", inline=False)
                embed.set_footer(text="不具合等連絡先: @bz6  開発: Branch Labs")
                await message.reply(embed=embed)
                response = gpt(message.content, 0, history, ai_data[1])


            # 履歴保存
            if len(response) > 0:
              if response[0] == True:
                
                # 文章モードのみ履歴保存
                if (len(response[1]) > 0) and (flag == 0):
                  user_dict = {"role": "user", "parts": [message.content]}
                  model_dict = {"role": "model", "parts": [response[1]]}

                  # 30件を超えたら削除（1個目はメッセージカウント）
                  if len(ai_data) >= 31:
                    del ai_data[2]
                    del ai_data[2]
                  
                  ai_data.append(user_dict)
                  ai_data.append(model_dict)

                  ai_data[0] += 1

                  with open(f'data/ai/{message.author.id}.json', 'w', encoding='UTF-8') as f:
                    json.dump(ai_data, f)
                
                  if len(response) > 1000:
                    response = response[1][:1000] + "\n\n※1000文字を超える内容は省略されました※"

                  else:
                    response = response[1]

                  await message.reply(response, mention_author=False)

                # 画像モード
                elif (len(response[1]) > 0) and (flag == 1):
                  ai_data[0] += 1
                  
                  with open(f'data/ai/{message.author.id}.json', 'w', encoding='UTF-8') as f:
                    json.dump(ai_data, f)

                  if len(response) > 1000:
                    response = response[1][:1000] + "\n\n※1000文字を超える内容は省略されました※"

                  else:
                    response = response[1]

                  await message.reply(response, mention_author=False)
                
                  
              else:
                if str(response[1]).startswith("429"):
                  embed = discord.Embed(title="混雑中",
                                      description="Amadeusが混雑しています。**5秒程度**お待ちください。", color=0xff0000)
                  embed.set_footer(text=f"Report ID: {message.id}")
                  await message.reply(embed=embed, mention_author=False)

                elif str(response[1]).startswith("500"):
                  embed = discord.Embed(title="混雑中またはエラー",
                                      description="サーバーが混雑しているか、内部エラーが発生しています。\n**30分～1時間程度**時間を空けると完全に解決される場合がありますが、このままご利用いただけます。", color=0xff0000)
                  embed.set_footer(text=f"Report ID: {message.id}")
                  await message.reply(embed=embed, mention_author=False)

                # エラー発生時
                else:
                  embed = discord.Embed(title="エラー",
                                      description="不明なエラーが発生しました。しばらく時間を空けるか、メッセージ内容を変えてください。", color=0xff0000)
                  embed.set_footer(text=f"Report ID: {message.id}")
                  await message.reply(embed=embed, mention_author=False)

                if message.attachments:
                  value = "（画像）"

                else:
                  value = message.content

                # エラーを専用チャンネルに投げておく async内じゃないので今は動かない
                error_log = client.get_channel(ERROR_LOG)
                embed = discord.Embed(title="エラー",
                                      description="Amadeus AIチャットにてエラーが発生しました。",
                                      timestamp=datetime.datetime.now(), color=0xff0000)
                embed.add_field(name="メッセージ内容",value=value)
                embed.add_field(name="エラー内容",value=response[1])
                embed.add_field(name="ギルドとチャンネル",value=f"{message.guild.name} (ID: {message.guild.id})\n#{message.channel.id}")
                embed.add_field(name="ユーザー",value=f"{message.author.mention} (ID: {message.author.id})")
                embed.set_footer(text=f"Report ID: {message.id}")
                await error_log.send(embed=embed)

  else:
      if message.content.startswith("::") or message.content.startswith("//") or message.content.startswith(prefix):
        pass

      else:
        with open(f"data/banned.txt", "r") as f:
          data = f.read().splitlines()

        if str(message.author.id) in data:
          embed = discord.Embed(title=":x: エラー",
                                description="あなたは管理者によって利用制限(BAN)されています。",
                                color=0xff0000)
          await message.reply(embed=embed, mention_author=False)

        else:
          async with message.channel.typing():
            # 画像データかどうか（画像は過去ログ使用不可）
            if message.attachments:
              flag = 1
              
              for attachment in message.attachments:
                # 対応している画像形式なら処理
                if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                    async with aiohttp.ClientSession() as session:
                        async with session.get(attachment.url) as resp:
                            if resp.status != 200:
                                await message.reply(":x: 画像が読み取れません。時間を空けてから試してください。", mention_author=False)
                                res = ""

                            else:
                              image_data = await resp.read()

                              bracket_pattern = re.compile(r'<[^>]+>')
                              cleaned_text = bracket_pattern.sub('', message.content)

                              if os.path.isfile(f"data/ai/{message.author.id}.json"):
                                with open(f"data/ai/{message.author.id}.json", "r", encoding='UTF-8') as f:
                                  ai_data = json.load(f)

                                chara = ai_data[1]

                              else:
                                chara = 0
                                ai_data = [0, 0]

                                with open(f'data/ai/{message.author.id}.json', 'w', encoding='UTF-8') as f:
                                    json.dump(ai_data, f)

                                embed = discord.Embed(title="Amadeus ヘルプ",
                                description="Amadeusのご利用ありがとうございます。",
                                color=discord.Colour.red())
                                embed.add_field(name="機能紹介",value=f"・アマデウス紅莉栖との会話\n・画像認識\n・`/count`と送信して会話回数の表示", inline=False)
                                embed.add_field(name="注意事項",value=f"**・Botへのメッセージ送信（#amadeus-chatでの送信含む）をもって、Branch Labsの[利用規約](https://host.zcen.net/satw/labs)に同意したものとなります。**\n・AIと会話しない場合は、メッセージの先頭に`::`または`//`を付けてください。\n・会話履歴はアマデウス紅莉栖と各ユーザー間で保存されます（直近30件まで）。他のユーザーとの会話に割り込むことはできません。\n・会話に不調を感じる場合は、`/clear`と送信し、会話履歴をリセットしてください。\n・Discord規約や公序良俗に反する発言を行ったり、アマデウス紅莉栖にそのような発言を促す行為を禁止します。", inline=False)
                                embed.add_field(name="専用コマンド",value=f"`{'/clear'.ljust(10)}` 会話履歴のリセット\n`{'/stats'.ljust(10)}` 統計情報の表示", inline=False)
                                embed.set_footer(text="不具合等連絡先: @bz6  開発: Branch Labs")
                                await message.reply(embed=embed)

                              response = gpt(cleaned_text, 1, image_data, chara)

                else:
                  await message.reply(":x: 画像が読み取れません。ファイルを変更してください。\n対応しているファイル形式: ```.png .jpg .jpeg .gif .webp```", mention_author=False)
                  response = ""
                            
            else:
              # 過去データ読み取り
              flag = 0

              # 会話したことがあるか
              if os.path.isfile(f"data/ai/{message.author.id}.json"):
                
                with open(f"data/ai/{message.author.id}.json", "r", encoding='UTF-8') as f:
                  ai_data = json.load(f)

                if len(ai_data) == 2:
                  history = []

                elif len(ai_data) >= 32:
                  history = list(ai_data[-30:])

                else:
                  history = list(ai_data[2:])
                  
                #print(history)
                response = gpt(message.content, 0, history, ai_data[1])

              # 会話が初めてならpkl作成＆インストラクション
              else:
                ai_data = [0, 0]
                history = []

                with open(f'data/ai/{message.author.id}.json', 'w', encoding='UTF-8') as f:
                    json.dump(ai_data, f)

                embed = discord.Embed(title="Amadeus ヘルプ",
                description="Amadeusのご利用ありがとうございます。",
                color=discord.Colour.red())
                embed.add_field(name="機能紹介",value=f"・アマデウス紅莉栖との会話\n・画像認識\n・`/count`と送信して会話回数の表示", inline=False)
                embed.add_field(name="注意事項",value=f"**・Botへのメッセージ送信（#amadeus-chatでの送信含む）をもって、Branch Labsの[利用規約](https://host.zcen.net/satw/labs)に同意したものとなります。**\n・AIと会話しない場合は、メッセージの先頭に`::`または`//`を付けてください。\n・会話履歴はアマデウス紅莉栖と各ユーザー間で保存されます（直近30件まで）。他のユーザーとの会話に割り込むことはできません。\n・会話に不調を感じる場合は、`/clear`と送信し、会話履歴をリセットしてください。\n・Discord規約や公序良俗に反する発言を行ったり、アマデウス紅莉栖にそのような発言を促す行為を禁止します。", inline=False)
                embed.add_field(name="専用コマンド",value=f"`{'/clear'.ljust(10)}` 会話履歴のリセット\n`{'/stats'.ljust(10)}` 統計情報の表示", inline=False)
                embed.set_footer(text="不具合等連絡先: @bz6  開発: Branch Labs")
                await message.reply(embed=embed)
                response = gpt(message.content, 0, history, ai_data[1])


            # 履歴保存
            if len(response) > 0:
              if response[0] == True:
                
                # 文章モードのみ履歴保存
                if (len(response[1]) > 0) and (flag == 0):
                  user_dict = {"role": "user", "parts": [message.content]}
                  model_dict = {"role": "model", "parts": [response[1]]}

                  # 30件を超えたら削除（1個目はメッセージカウント）
                  if len(ai_data) >= 31:
                    del ai_data[2]
                    del ai_data[2]
                  
                  ai_data.append(user_dict)
                  ai_data.append(model_dict)

                  ai_data[0] += 1

                  with open(f'data/ai/{message.author.id}.json', 'w', encoding='UTF-8') as f:
                    json.dump(ai_data, f)
                
                  if len(response) > 1000:
                    response = response[1][:1000] + "\n\n※1000文字を超える内容は省略されました※"

                  else:
                    response = response[1]

                  await message.author.send(response)

                # 画像モード
                elif (len(response[1]) > 0) and (flag == 1):
                  ai_data[0] += 1
                  
                  with open(f'data/ai/{message.author.id}.json', 'w', encoding='UTF-8') as f:
                    json.dump(ai_data, f)

                  if len(response) > 1000:
                    response = response[1][:1000] + "\n\n※1000文字を超える内容は省略されました※"

                  else:
                    response = response[1]

                  await message.author.send(response)
                
                  
              else:
                if str(response[1]).startswith("429"):
                  embed = discord.Embed(title="混雑中",
                                      description="Amadeusが混雑しています。**5秒程度**お待ちください。", color=0xff0000)
                  embed.set_footer(text=f"Report ID: {message.id}")
                  await message.author.send(embed=embed)

                elif str(response[1]).startswith("500"):
                  embed = discord.Embed(title="混雑中またはエラー",
                                      description="サーバーが混雑しているか、内部エラーが発生しています。\n**30分～1時間程度**時間を空けると完全に解決される場合がありますが、このままご利用いただけます。", color=0xff0000)
                  embed.set_footer(text=f"Report ID: {message.id}")
                  await message.author.send(embed=embed)

                # エラー発生時
                else:
                  embed = discord.Embed(title="エラー",
                                      description="不明なエラーが発生しました。しばらく時間を空けるか、メッセージ内容を変えてください。", color=0xff0000)
                  embed.set_footer(text=f"Report ID: {message.id}")
                  await message.send(embed=embed)

                if message.attachments:
                  value = "（画像）"

                else:
                  value = message.content

                # エラーを専用チャンネルに投げておく async内じゃないので今は動かない
                error_log = client.get_channel(ERROR_LOG)
                embed = discord.Embed(title="エラー",
                                      description="Amadeus AIチャットにてエラーが発生しました。",
                                      timestamp=datetime.datetime.now(), color=0xff0000)
                embed.add_field(name="メッセージ内容",value=value)
                embed.add_field(name="エラー内容",value=response[1])
                embed.add_field(name="ギルドとチャンネル",value=f"DM")
                embed.add_field(name="ユーザー",value=f"{message.author.mention} (ID: {message.author.id})")
                embed.set_footer(text=f"Report ID: {message.id}")
                await error_log.send(embed=embed)


  if message.author.id == OWNER:
    if message.content == f"{prefix}devhelp":
      desc = f"```Amadeus 管理者用コマンドリスト```\n**管理コマンド**\n`sync`, `devsync`, `ban`, `unban`"
      embed = discord.Embed(title="📖コマンドリスト", description=desc)
      await message.reply(embed=embed, mention_author=False)

    if message.content == f"{prefix}sync":
      #コマンドをSync
      try:
        await tree.sync()

      except Exception as e:
        embed = discord.Embed(title=":x: エラー",description="コマンドのSyncに失敗しました",color=0xff0000)
        embed.add_field(name="エラー内容",value=e)
        await message.reply(embed=embed, mention_author=False) 

      else:
        embed = discord.Embed(title=":white_check_mark: 成功",
                            description="コマンドのSyncに成功しました",
                            color=discord.Colour.green())
        await message.reply(embed=embed, mention_author=False)

    if message.content == f"{prefix}devsync":
      #コマンドをSync
      try:
        await tree.sync(guild=message.guild.id)

      except Exception as e:
        embed = discord.Embed(title=":x: エラー",description="コマンドのSyncに失敗しました",color=0xff0000)
        embed.add_field(name="エラー内容",value=e)
        await message.reply(embed=embed, mention_author=False) 

      else:
        embed = discord.Embed(title=":white_check_mark: 成功",
                            description="コマンドのSyncに成功しました",
                            color=discord.Colour.green())
        await message.reply(embed=embed, mention_author=False)

    if message.content == f"{prefix}stop":
      print("[Info] Shutdown is requested by owner")
      embed = discord.Embed(title=":white_check_mark: 成功",
                            description="Amadeusをシャットダウンしています",
                            color=discord.Colour.green())
      await message.reply(embed=embed, mention_author=False)
      await client.close()

    if message.content.startswith(f"{prefix}ban"):
      with open(f"data/banned.txt", "r") as f:
        data = f.read().splitlines()

      try:
        args = message.content.split()

        if str(args[1]) in data:
          embed = discord.Embed(title=":x: エラー",description="そのユーザーは既にBANされています", color=0xff0000)
          await message.reply(embed=embed, mention_author=False) 

        else:
          data.append(str(args[1]))
          data = "\n".join(data)

          with open(f"data/banned.txt", "w") as f:
              f.write(data)

          embed = discord.Embed(title=":white_check_mark: 成功",
                              description="ユーザーのBANに成功しました",
                              color=discord.Colour.green())
          embed.add_field(name="対象者", value=f"<@{args[1]}> (ID: {args[1]})", inline=False)
          await message.reply(embed=embed, mention_author=False)
          
      except Exception as e:
        embed = discord.Embed(title=":x: エラー",description="ユーザーのBANに失敗しました", color=0xff0000)
        embed.add_field(name="エラー内容",value=e)
        await message.reply(embed=embed, mention_author=False)

    if message.content.startswith(f"{prefix}unban"):
          with open(f"data/banned.txt", "r") as f:
            data = f.read().splitlines()

          try:
            args = message.content.split()

            if str(args[1]) not in data:
              embed = discord.Embed(title=":x: エラー",description="そのユーザーはBANされていません", color=0xff0000)
              await message.reply(embed=embed, mention_author=False) 

            else:
              data.remove(str(args[1]))

              with open(f"data/banned.txt", "w") as f:
                  for i in data:
                    f.write("%s\n" % i)
                  
              embed = discord.Embed(title=":white_check_mark: 成功",
                                  description="ユーザーのBANを解除しました",
                                  color=discord.Colour.green())
              embed.add_field(name="対象者", value=f"<@{args[1]}> (ID: {args[1]})", inline=False)
              await message.reply(embed=embed, mention_author=False)
              
          except Exception as e:
            embed = discord.Embed(title=":x: エラー",description="ユーザーのBAN解除に失敗しました", color=0xff0000)
            embed.add_field(name="エラー内容",value=e)
            await message.reply(embed=embed, mention_author=False) 


#Botの起動とDiscordサーバーへの接続
client.run(TOKEN)
