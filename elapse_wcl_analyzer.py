#coding=utf-8

import requests
import json
import os, sys, getopt
import csv
import pandas as pd
from requests import NullHandler, models  
from python_graphql_client import GraphqlClient

TOKEN_URL = 'https://www.warcraftlogs.com/oauth/token'
WCLV2_URL = "https://www.warcraftlogs.com/api/v2/client"

IGNORE_ENCOUNTERS = ['Morogrim Tidewalker']
IGNORE_PLAYERS = []

GL_ALL_FIGHTS_LIST = list()
GL_ALL_KILLS_LIST = list()
GL_ALL_RANKING_LIST = list()
GL_ELAPSE_FIGHT_RANKING = list()
GL_FIGHT_DPS_LIST = list()
GL_ALL_DPS_LIST = list()
GL_HEALER_LIST = list()
GL_PLAYER_ACTOR_MAP = dict()
GL_DPS_CATALOG = {
    'melee':[
        {'Paladin':'Retribution'},
        {'Rogue':'*'},
        {'Shaman':'Enhancement'},
        {'Warrior':'*'}
    ], 
    'range':[
        {'Shaman':'Elemental'},
        {'Priest':'Shadow'},
        {'Mage':'*'},
        {'Druid':'Balance'},
        {'Warlock':'*'}
    ], 
    'range-melee':[
        {'Hunter':'*'}
    ]
    }

# 加速，毁灭，风暴大蓝，水库大蓝，大蓝
DPS_POTION_CHECK = {
                        28507:"加速",
                        28508:"毁灭",   
                        41617:"恢复法力",
                        41618:"恢复法力",
                        28499:"恢复法力",
                    }
# 风暴大蓝，水库大蓝，大蓝
HEALER_POTION_CHECK = {
                        41617:"恢复法力",
                        41618:"恢复法力",
                        28499:"恢复法力"
                    }


def _get_token(auth64str:str) -> str:
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

def get_raid_fight(wcl_report_link: str, client: GraphqlClient) -> None:
    # Repor ID: e.g. rwG81bzxZvg3mDN9 
    report_code = wcl_report_link.split('/')[-1]

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

    #Set for global use
    global GL_ALL_FIGHTS_LIST
    global GL_ALL_KILLS_LIST
    GL_ALL_FIGHTS_LIST = all_fights_list
    GL_ALL_KILLS_LIST = kills_fights_id_list

def get_rankings(wcl_report_link: str, client: GraphqlClient) -> None:
    # Repor ID: e.g. rwG81bzxZvg3mDN9 
    report_code = wcl_report_link.split('/')[-1]

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
    global GL_ALL_RANKING_LIST
    GL_ALL_RANKING_LIST = all_rankings_list
    #print(all_rankings_json)

def get_dps_parse_and_bracket(wcl_report_link: str, client: GraphqlClient) -> None:
    # Repor ID: e.g. rwG81bzxZvg3mDN9 
    report_code = wcl_report_link.split('/')[-1]

    #DPS Ranks model
    # [{boss1:[{name:player1,class:pal,parse:87,item:66},{name:player1,class:pal,parse:87,item:66}]},...]
    elapse_ranking = dict()

    all_rankings_list = GL_ALL_RANKING_LIST

    #Get DPS fights ranks
    kills_fights_id_arr = list()
    dps_players = list()
    fight_dps_player_with_class = dict()
    boss_name = list()
    kills_fights_id_list = GL_ALL_KILLS_LIST
    for i in kills_fights_id_list:
        kills_fights_id_arr.append(i['id'])
    for r in all_rankings_list:
        if r['encounter']['name'] in IGNORE_ENCOUNTERS:
            continue
        if r['fightID'] in kills_fights_id_arr:
            boss = r['encounter']['name']
            dps_list = r['roles']['dps']['characters']
            boss_name.append(boss)
            boss_dps_list = list()
            fight_dps_player_list = list()
            for d in dps_list:
                if d['name'] not in IGNORE_PLAYERS:
                    player_name = d['name']
                    player_class = d['class']
                    player_parse = d['rankPercent']
                    player_bracket = d['bracketPercent']
                    player_spec = d['spec']
                    player_dict = dict()
                    player_dict['name'] = player_name
                    dps_players.append(player_name)
                    fight_dps_player_list.append({player_name:"{}|{}".format(player_class,player_spec)})
                    player_dict['class'] = player_class
                    player_dict['parse'] = player_parse
                    player_dict['bracket'] = player_bracket
                    boss_dps_list.append(player_dict)
            fight_dps_player_with_class[boss] = fight_dps_player_list
            elapse_ranking[boss]=boss_dps_list
    
    #print(json.dumps(elapse_ranking))
    # Should form the metrix here other than
    # build a metrix col ->           boss1, boss2 avg
    #                row -> player1   p+b    p+b   player1-avg
    #                       player2   
    #                       boss-avg  b-avg        benchmark-avg
    # if player does not show in bossX, use 0
    dps_players_global = list(set(dps_players))
    global GL_FIGHT_DPS_LIST
    GL_FIGHT_DPS_LIST = dps_players_global
    boss_name = list(set(boss_name))

    global GL_DPS_PLAYER_WITH_CLASS
    GL_DPS_PLAYER_WITH_CLASS = fight_dps_player_with_class 

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
    elapse_score = list()
    for p in dps_players_global:
        p_score_dict = dict()
        p_score_dict['name'] = p
        participants_count = 0
        participants_sum_score = 0
        participants_sum_prase = 0
        participants_sum_bracket = 0
        for encounter, dps_player_list in elapse_ranking.items():
            dps_participants = list()
            for dps in dps_player_list:
                dps_participants.append(dps['name']) 
            if p in dps_participants:
                for pp in dps_player_list:
                    if p == pp['name']:
                        parse = pp['parse']
                        bracket = pp['bracket']
                        pclass = pp['class']
                p_score_dict['class'] = pclass
                score = parse + bracket
                participants_sum_score = participants_sum_score + score
                participants_sum_prase = participants_sum_prase + parse
                participants_sum_bracket = participants_sum_bracket + bracket
                participants_count = participants_count + 1
            else:
                score = 0
                parse = 0
                bracket = 0
            p_score_dict["{}-parse".format(encounter)] = parse
            p_score_dict["{}-bracket".format(encounter)] = bracket
            p_score_dict[encounter] = score
        p_score_dict['mean-parse'] = participants_sum_prase / participants_count
        p_score_dict['mean-bracket'] = participants_sum_bracket / participants_count
        p_score_dict['mean'] = participants_sum_score / participants_count
        elapse_score.append(p_score_dict)
    #print(elapse_score)
            # print("|-{} {}".format(encounter,score))

    # Reuse style 2 for mean score per encounter
    encounter_mean_dict = dict()
    encounter_mean_dict['name'] = 'Total'
    encounter_mean_dict['class'] = 'dps'
    elapse_total_score = 0
    elapse_total_parse = 0
    elapse_total_bracket = 0
    for encounter, dps_player_list in elapse_ranking.items():
        #print(encounter)
        dps_participants = list()
        encounter_total_score = 0
        encounter_total_parse = 0
        encounter_total_bracket = 0
        for dps in dps_player_list:
            dps_participants.append(dps['name'])
        for p in dps_players_global:
            if p in dps_participants:
                for pp in dps_player_list:
                    if p == pp['name']:
                        parse = pp['parse']
                        bracket = pp['bracket']
                score = parse + bracket
                encounter_total_score = encounter_total_score + score
                encounter_total_parse = encounter_total_parse + parse
                encounter_total_bracket = encounter_total_bracket + bracket
        encounter_mean = encounter_total_score / len(dps_participants)
        encounter_mean_parse = encounter_total_parse / len(dps_participants)
        encounter_mean_bracket = encounter_total_bracket / len(dps_participants)

        elapse_total_score = elapse_total_score + encounter_mean
        elapse_total_parse = elapse_total_parse + encounter_mean_parse
        elapse_total_bracket = elapse_total_bracket + encounter_mean_bracket
        encounter_mean_dict[encounter] = encounter_mean
        encounter_mean_dict["{}-parse".format(encounter)] = encounter_mean_parse
        encounter_mean_dict["{}-bracket".format(encounter)] = encounter_mean_bracket
            #print("|-{} {}".format(p,score))
    elapse_mean = elapse_total_score / len(boss_name)
    elapse_mean_parse = elapse_total_parse / len(boss_name)
    elapse_mean_bracket = elapse_total_bracket / len(boss_name)
    encounter_mean_dict['mean'] = elapse_mean
    encounter_mean_dict['mean-parse'] = elapse_mean_parse
    encounter_mean_dict['mean-bracket'] = elapse_mean_bracket

    elapse_score.append(encounter_mean_dict)

    df = pd.DataFrame(elapse_score) 
    
    # saving the dataframe 
    df.to_csv('elapse_score.csv', encoding='utf_8_sig') 

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

def get_raid_actor(wcl_report_link: str, client: GraphqlClient) -> None:
    # Repor ID: e.g. rwG81bzxZvg3mDN9 
    report_code = wcl_report_link.split('/')[-1]

    # Step 4 - Get Player Fight Ranks
    actor_query="""
        query {
            reportData {
                report(code: "%s") {
                    masterData{
                        actors(type:"Player"){
                            name
                            id
                        }
                    }
                }
            }
        }
    """%report_code
    all_actor_data = client.execute(query=actor_query)
    actor_list = all_actor_data['data']['reportData']['report']['masterData']['actors']
    
    player_list = list()
    healer_list = list()
    dps_list = list()
    tank_list = list()
    #Parse Raid Tank & Healer
    for r in GL_ALL_RANKING_LIST:
        r_dps_list = r['roles']['dps']['characters']
        r_tank_list = r['roles']['tanks']['characters']
        r_healer_list = r['roles']['healers']['characters']
        for t in r_tank_list:
            if t['name'] not in IGNORE_PLAYERS:
                player_name = t['name']
                tank_list.append(player_name)
        for h in r_healer_list:
            if h['name'] not in IGNORE_PLAYERS:
                player_name = h['name']
                healer_list.append(player_name)
        for d in r_dps_list:
            if d['name'] not in IGNORE_PLAYERS:
                player_name = d['name']
                dps_list.append(player_name)

    player_list = healer_list+dps_list+tank_list
    player_list = list(set(player_list))
    global GL_ALL_DPS_LIST
    global GL_HEALER_LIST
    GL_ALL_DPS_LIST = list(set(dps_list))
    GL_HEALER_LIST = list(set(healer_list))

    global GL_PLAYER_ACTOR_MAP
    for p in player_list:
        for n in actor_list:
            if str(p) == str(n['name']):
                GL_PLAYER_ACTOR_MAP[p]=n['id']
   
def get_dps_fight_potion(wcl_report_link: str, client: GraphqlClient) -> None:
    # Repor ID: e.g. rwG81bzxZvg3mDN9 
    report_code = wcl_report_link.split('/')[-1]
    # Prepare:
    # DPS Player List encounters only - GL_DPS_LIST 
    # Potions in count - DPS_POTION_CHECK
    # FightID with startTime and endTime in GL_ALL_KILLS_LIST
    if not GL_ALL_KILLS_LIST:
        return
    if not GL_FIGHT_DPS_LIST:
        return
    
    # Output model
    # {
    #     player1: [{name:encounter1, mana:5, haste:2, ...},{name:encounter2, mana:2, haste:1}...],
    #     player2: [],
    #     ...
    # }

    # query model for single player
    # 0) Find player actorID in gameMasterData
    # 1) query player P as sourceID(actoerID) in fightID x (startTime->endTime), dataType:Casts in events.
    # 2) if nextPageTimestamp != null, loop 1) with startTime again till not nextPageTimestamp
    # query {
	# reportData {
	# 	report(code: "rwG81bzxZvg3mDN9") {
    #         events(
    #             startTime:14089632,
    #             endTime:14920070,
    #             dataType:Casts,
    #             useActorIDs:false,
    #             sourceID:23){
    #             nextPageTimestamp
    #             data
    #             }
    #         }
    #     }
    # }
    dps_potion_list = list()
    for p in GL_FIGHT_DPS_LIST:
        player_potion_dict = dict()
        player_potion_dict['name'] = p
        print("|-[INFO] Getting {} info...".format(p))
        for f in GL_ALL_KILLS_LIST:
            player_fight_potion_dict = dict()
            player_fight_potion_dict[f['name']] = list()
            aggregate_d = dict()
            print("|--[INFO] Getting {} info in kills {}...".format(p,f['name']))
            for a_id,a_name in DPS_POTION_CHECK.items():
                print("|---[INFO] Counting {}:{} ...".format(a_id,a_name))
                # aggregate_d[a_name] = 0 
                aggregate_l = list()
                aggregate_dist = list()
                sourceID = GL_PLAYER_ACTOR_MAP[p]
                start = f['startTime']
                end = f['endTime']
                cast_list = _get_player_cast(report_code, int(start), int(end), sourceID, a_id, client)
                # print("{} - {}".format(p , f['name']))
                if cast_list:
                    aggregate_d[a_name] = 0 
                    # [{'timestamp': 13683470, 'type': 'cast', 'sourceID': 21, 'targetID': -1, 'abilityGameID': 41618},...]
                    for cast in cast_list:
                        cast.pop('type')
                        cast.pop('targetID')
                        cast.pop('sourceID')
                        cast.pop('sourceMarker','no sourceMarker')
                        id = cast['abilityGameID']
                        cast.pop('timestamp')
                        cast['abilityGameID'] = a_name
                    aggregate_d[a_name] = aggregate_d[a_name] + len(cast_list)
                    aggregate_l.append(aggregate_d)
                    print(aggregate_l)
                    aggregate_dist = [dict(t) for t in {tuple(sorted(d.items())) for d in aggregate_l}]
                    player_fight_potion_dict[f['name']] = [*player_fight_potion_dict[f['name']],*aggregate_dist]
                    # print(player_fight_potion_dict[f['name']])

            player_potion_dict = {**player_potion_dict, **player_fight_potion_dict}
        dps_potion_list.append(player_potion_dict)
        # print(player_potion_dict)
    df = pd.DataFrame(dps_potion_list) 
    df.to_csv('elapse_dps_potion.csv', encoding='utf_8_sig') 



def _get_player_cast(report_code:str, start:float, end:float, actorID:int, abilityID:int, client: GraphqlClient) -> list:
    player_cast_list = list()
    
    nextPageTimestamp = start
    while nextPageTimestamp:
        dps_fight_casts_query = """
            query {
                reportData {
                    report(code: "%(code)s") {
                        events(
                            startTime:%(start)s,
                            endTime:%(end)s,
                            dataType:Casts,
                            useActorIDs:false,
                            abilityID:%(ability)s,
                            sourceID:%(actor)s)
                        {
                            nextPageTimestamp
                            data
                        }
                    }
                }
            }
        """%{"code":report_code, "start":nextPageTimestamp, "end":end, "actor":actorID, "ability":abilityID}
        player_cast = client.execute(query=dps_fight_casts_query)
        try:
            cast_data = player_cast['data']['reportData']['report']['events']['data']
            player_cast_list = [*player_cast_list ,*cast_data]
        except(KeyError):
            print("No data found, skip...")
        nextPageTimestamp = player_cast['data']['reportData']['report']['events']['nextPageTimestamp']
    return player_cast_list







    




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
    
    # Get Client
    print("[INFO]Initilizing wcl client")
    client = gql_client(_get_token(None))

    # Prepare:
    print("[INFO]Getting all fights in given report")
    get_raid_fight(wcl_report_link, client)
    print("[INFO]Getting all player ranks in given report")
    get_rankings(wcl_report_link, client)
    print("[INFO]Getting all player as actors in given report")
    get_raid_actor(wcl_report_link, client)

    # Usage 1 - Parse + Bracket
    print("[INFO]Generating dps player parse and bracket level in csv")
    get_dps_parse_and_bracket(wcl_report_link, client)

    # Usage 2 - DPS Player Potion in all encounter fights
    print("[INFO]Generating dps player potion in csv")
    get_dps_fight_potion(wcl_report_link, client)


# Step 5 - Get Player Fight Potion

# Step 6 - Get Healer Casts - Entire Raid

# Step 7 - Get Overhealed Volume % - Entire Raid

# Step 8 - Get Healer Potion - Entire Raid

