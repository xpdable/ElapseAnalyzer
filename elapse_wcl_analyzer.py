import requests
import json
import os, sys, getopt
import csv
from python_graphql_client import GraphqlClient

TOKEN_URL = 'https://www.warcraftlogs.com/oauth/token'
WCLV2_URL = "https://www.warcraftlogs.com/api/v2/client"

def _get_token(auth64str: str) -> str:
    if not auth64str:
        key = 'WCL_CLIENT_TOKEN'
        base64authstr = os.getenv(key)
    else:
        base64authstr = auth64str

    #TODO raise expection for none token

    token_data = 'grant_type=client_credentials'
    token_header = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Basic {}'.format(base64authstr)
    }
    token_resp = requests.request("POST", TOKEN_URL, headers=token_header,  data=token_data)
    token_json = json.loads(token_resp.text)
    token = token_json['access_token']
    return token

def gql_client(bearer_token:str) -> GraphqlClient: 
    qheader = {
        'Content-Type' : 'application/json',
        'Authorization' : 'Bearer {}'.format(bearer_token)
    }
    return GraphqlClient(endpoint=WCLV2_URL, headers=qheader)


if __name__ == '__main__':

    # Get Single Report
    # Option 1 - via report link https://cn.classic.warcraftlogs.com/reports/rwG81bzxZvg3mDN9 or the code rwG81bzxZvg3mDN9 
    # TODO Option 2 - via guild code and report title

    inputopts, args = getopt.getopt(sys.argv[1:],"h:l:gt")
    for o, val in inputopts:
        if o == '-h':
            print("help") #TODO
        elif o == '-l':
            wcl_report_link=val
        elif o == '-t':
            wcl_report_title=val
        elif o == '-g':
            wcl_guild_name=val	
        else:
            print("wrong args")

    if not wcl_report_link:
        #TODO option2 find report by guild name and title
        print("TODO")

    # Repor ID: e.g. rwG81bzxZvg3mDN9 
    report_code = wcl_report_link.split('/')[-1]

    client = gql_client(_get_token(None))

    # Step 3 - Get Fights
    # Get Report All Fights
    # killType {Encounters=={Kills+Wipes},Kills==true,Wipes==false,Trash==null}
    # translate:true aligned as English
    all_fights_query = """
        query {
            reportData {
                report(code: "%s") {
                    fights(translate:true) {
                        id
                        name
                        kill
                        startTime
                        endTime
                    }
                }
            }
        }
    """%report_code

    all_fights_data = client.execute(query=all_fights_query)

    # {'data': {'reportData': {'report': {'fights': []
    # print(all_fights_data)
    all_fights_list = all_fights_data['data']['reportData']['report']['fights']
    kills_fights_id_list = list()
    # 3.1 Select Fights
    for f in all_fights_list:
        if f['kill'] is True:
            kills_fights_id_list.append(f)
    #print(kills_fights_id_list)

    # Step 4 - Get Player Fight Ranks
    rankings_query="""
        query {
            reportData {
                report(code: "%s") {
                    rankings
                }
            }
        }
    """%report_code

    all_rankings_data = client.execute(query=rankings_query)
    # {'data': {'reportData': {'report': {'rankings': json
    all_rankings_list = all_rankings_data['data']['reportData']['report']['rankings']['data']
    #print(all_rankings_json)

    #DPS Ranks model
    # [{boss1:[{name:player1,class:pal,parse:87,item:66},{name:player1,class:pal,parse:87,item:66}]},...]
    elapse_ranking = dict()

    #Get DPS fights ranks
    kills_fights_id_arr = list()
    dps_players = list()
    boss_name = list()
    for i in kills_fights_id_list:
        kills_fights_id_arr.append(i['id'])
    for r in all_rankings_list:
        if r['fightID'] in kills_fights_id_arr:
            boss = r['encounter']['name']
            dps_list = r['roles']['dps']['characters']
            boss_name.append(boss)
            boss_dps_list = list()
            for d in dps_list:
                player_name = d['name']
                player_class = d['class']
                player_parse = d['rankPercent']
                player_bracket = d['bracketPercent']
                player_dict = dict()
                player_dict['name'] = player_name
                dps_players.append(player_name)
                player_dict['class'] = player_class
                player_dict['parse'] = player_parse
                player_dict['bracket'] = player_bracket
                boss_dps_list.append(player_dict)
            elapse_ranking[boss]=boss_dps_list
    
    #print(json.dumps(elapse_ranking))
    # Should form the metrix here other than
    # build a metrix col ->           boss1, boss2 avg
    #                row -> player1   p+b    p+b   player1-avg
    #                       player2   
    #                       boss-avg  b-avg        benchmark-avg
    # if player does not show in bossX, use 0
    dps_players_global = list(set(dps_players))
    boss_name = list(set(boss_name))

    # Style 1 Player per Encounters
    # 止戈之战
    # |-Hydross the Unstable 193
    # |-The Lurker Below 198
    # |-Leotheras the Blind 188
    # |-Fathom-Lord Karathress 194
    # |-Morogrim Tidewalker 185
    # |-Lady Vashj 186
    # |-A'lar 196
    # |-Void Reaver 191
    # |-High Astromancer Solarian 141
    # |-Kael'thas Sunstrider 164
    for p in dps_players_global:
        print(p)
        for encounter, dps_player_list in elapse_ranking.items():
            dps_participants = list()
            for dps in dps_player_list:
                dps_participants.append(dps['name']) 
            if p in dps_participants:
                for pp in dps_player_list:
                    if p == pp['name']:
                        parse = pp['parse']
                        bracket = pp['bracket']
                score = parse + bracket
            else:
                score = 0
            # print("|-{} {}".format(encounter,score))


    # Style 2 Encounter per player
    # Kael'thas Sunstrider
    # |-同舟共济 176
    # |-吃素的尼姑 108
    # |-黑鼻子 183
    # |-小小星痕 150
    # |-蓝条狂暴战 139
    # |-妖应封光 160
    # |-老衲不吃肥肉 155
    # |-Richturteil 0
    # |-Lolit 165
    # |-神之无之 139
    # |-莉莉科林斯 30
    # |-荀文若 75
    # |-鲁德彪 0
    # |-Galgadòt 18
    # |-雾染霜华 0
    # |-强彡森 111
    # |-神卡布 0
    # |-屁神久我 71
    # |-止戈之战 164
    # |-慕蔺 18
    # for encounter, dps_player_list in elapse_ranking.items():
    #     print(encounter)
    #     dps_participants = list()
    #     for dps in dps_player_list:
    #         dps_participants.append(dps['name'])
    #     for p in dps_players_global:
    #         if p in dps_participants:
    #             for pp in dps_player_list:
    #                 if p == pp['name']:
    #                     parse = pp['parse']
    #                     bracket = pp['bracket']
    #             score = parse + bracket
    #         else:
    #             score = 0
    #         print("|-{} {}".format(p,score))

            

    #print(score)

    # 4.1 Print CSV
    # with open('boss_dps_ranking.csv', 'w') as f: 
    #     w = csv.writer(f)
    #     w.writerow(elapse_ranking)








# Synchronous request


# Step 5 - Get Player Fight Potion

# Step 6 - Get Healer Casts - Entire Raid

# Step 7 - Get Overhealed Volume % - Entire Raid

# Step 8 - Get Healer Potion - Entire Raid

