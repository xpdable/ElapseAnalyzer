import requests
import json
import os, sys, getopt
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

    client = gql_client(_get_token())

    # Get Report All Fights
    # killType {Encounters=={Kills+Wipes},Kills==true,Wipes==false,Trash==null}
    all_fights_query = """
        query {
        reportData {
            report(code: "{}") {
                fights(translate:false) {
                    id
                    name
                    kill
                }
            }
        }
    }
    """.format(report_code)
    all_fights_data = client.execute(query=all_fights_query)


# Step 2 - Get Fight Report

# Step 3 - Get Fights

# 3.1 Select Fights



# Step 4 - Get Player Fight Ranks


# Synchronous request


# Step 5 - Get Player Fight Potion

# Step 6 - Get Healer Casts - Entire Raid

# Step 7 - Get Overhealed Volume % - Entire Raid

# Step 8 - Get Healer Potion - Entire Raid

