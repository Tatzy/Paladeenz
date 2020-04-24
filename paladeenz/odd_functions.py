import json
import arrow

# Status codes from 'getplayerstatus'
# 0 - Offline
# 1 - In Lobby  (basically anywhere except god selection or in game)
# 2 - god Selection (player has accepted match and is selecting god before start of game)
# 3 - In Game (match has started)
# 4 - Online (player is logged in, but may be blocking broadcast of player state)
# 5 - Unknown (player not found)


def parse_rank(tier):
    ranks = {
        '0' : 'qual',
        '1' : 'b5', 
        '2' : 'b4', 
        '3' : 'b3', 
        '4' : 'b2', 
        '5' : 'b1', 
        '6' : 's5',
        '7' : 's4',
        '8' : 's3',
        '9' : 's2',
        '10' : 's1',
        '11' : 'g5',
        '12' : 'g4',
        '13' : 'g3', 
        '14' : 'g2', 
        '15' : 'g1', 
        '16' : 'p5',
        '17' : 'p4',
        '18' : 'p3',
        '19' : 'p2',
        '20' : 'p1',
        '21' : 'd5',
        '22' : 'd4',
        '23' : 'd3',
        '24' : 'd2',
        '25' : 'd1',
        '26' : 'master',
        '27' : 'gm'
    }
    return 'ranks/' + ranks[str(tier)] + '.png'
def parse_rank_name(tier):
    ranks = {
        '0' : 'qualifying',
        '1' : 'Bronze 5', 
        '2' : 'Bronze 4', 
        '3' : 'Bronze 3', 
        '4' : 'Bronze 2', 
        '5' : 'Bronze 1', 
        '6' : 'Silver 5',
        '7' : 'Silver 4',
        '8' : 'Silver 3',
        '9' : 'Silver 2',
        '10' : 'Silver 1',
        '11' : 'Gold 5',
        '12' : 'Gold 4',
        '13' : 'Gold 3', 
        '14' : 'Gold 2', 
        '15' : 'Gold 1', 
        '16' : 'Platinum 5',
        '17' : 'Platinum 4',
        '18' : 'Platinum 3',
        '19' : 'Platinum 2',
        '20' : 'Platinum 1',
        '21' : 'Diamond 5',
        '22' : 'Diamond 4',
        '23' : 'Diamond 3',
        '24' : 'Diamond 2',
        '25' : 'Diamond 1',
        '26' : 'Master',
        '27' : 'Grandmaster'
    }
    return ranks[str(tier)]

def parse_champion(champion):
    if champion == None:
        return "ERROR"    
    else:
        champ = champion.lower().replace(" ", "-")
        champ = champ.replace("\'","-")
        return 'champions/' + champ + '.jpg'
    
def parse_item(item):
    if item != "":
        item = item.lower().replace(" ", "-")
        item = "items/" + item + ".jpg"
        return item
    else:
        return ""
    


def parse_map(map_game):
    if map_game == None:
        return "ERROR"   
    else:
        map_game = map_game.replace("Ranked ", "")
        map_game = map_game.replace("LIVE ", "")
        map_game = map_game.replace(" ", "-")
        map_game = map_game.lower()
        map_game = 'maps/' + map_game + ".png"
        return map_game

def parse_map_name(map_game):
    if map_game == None:
        return "ERROR"   
    else:
        map_game = map_game.replace("LIVE ", "")
        return map_game

def get_player_status(name,session):
    player_stat = session._make_request('getplayerstatus', [name])
    if player_stat == []:
        return False
    elif player_stat[0]['status'] == 3:
        return player_stat[0]['Match']
    else:
        return player_stat[0]['status']

def player_live_lookup(match, session):
        match_details = session._make_request('getmatchplayerdetails',[match] )
        teamOne = []
        teamTwo = []
        first = True
        for player in match_details:
            if first:
                mapName = player['mapGame']
                first = False
            if player['ret_msg'] == None:
                try:
                    winrate = player['tierWins'] / (player['tierWins'] + player['tierLosses'])
                except:
                    winrate = 0
                if player['playerName'] == "":
                    playerdude = "[PRIVATE PROFILE]"
                else:
                    playerdude = player['playerName']
                p = {
                    'championName' : player['ChampionName'],
                    'champ_img' : parse_champion(player['ChampionName']),
                    'rank' : parse_rank(player['Tier']),
                    'rankName' : parse_rank_name(player['Tier']),
                    'winrate' : str(int(round(winrate,2)*100)) + "%",
                    'playerName' : playerdude
                }
                if player['taskForce'] == 1:
                    teamOne.append(p)
                else:
                    teamTwo.append(p)
        ### Very important object for livematch
        game_info = {
            'teamOne' : teamOne,
            'teamTwo' : teamTwo,
            'map_name' : parse_map_name(mapName),
            'map_image' : parse_map(mapName),
            'status' : 3,
            'error_msg' : "None"
        }

        return game_info

def get_recent_matches(s, player_id, t):
    match_history = s._make_request("getmatchhistory", [player_id])
    matches = []
    t = -int(t)/60
    if match_history != []:
        i = 0
        for match in match_history:
            if i == 10:
                break
            else:
                matches.append(str(match['Match']))
                i+=1
    all_match_info = s._make_request("getmatchdetailsbatch", [",".join(matches)])

    all_match_array = {}
    for match in all_match_info:

        match['match_type'] = match['Map_Game'].split(" ")[0]
        match['map_name'] = " ".join(match['Map_Game'].split(" ")[1:])
        match['champ_img'] = parse_champion(match['Reference_Name'])
        match['item1_img'] = parse_item(match["Item_Active_1"])
        match['item2_img'] = parse_item(match["Item_Active_2"])
        match['item3_img'] = parse_item(match["Item_Active_3"])
        new_time = arrow.get(match['Entry_Datetime'], "M/D/YYYY h:mm:ss A")
        new_time = new_time.shift(hours = int(t))
        new_time = new_time.format("MM/DD/YYYY h:mm A")
        match['Entry_Datetime'] = new_time

        if match["playerName"] == "":
            match["playerName"] = '[PRIVATE PROFILE]'
        if match['Match'] not in all_match_array.keys():
            all_match_array[match['Match']] = []
        match['status'] = 1
        all_match_array[match['Match']].append(match)
        
    if all_match_array != {}:
        return all_match_array
    else:
        return {'error_msg': "Player profile is private or does not exist.", 'status': 0}