""" This file contains methods that obtain data from the TBA API """

import json
import datetime
from datetime import date, timedelta
from api_manager import call
from pathlib import Path
import functools

API_URL = "https://www.thebluealliance.com/api/v3/"
HEADER = {
        "X-TBA-Auth-Key": "NvwzlQxqO6BHmjT2cHdNDdgZlQSxdvbMrc8DiP7saThVURWSdtYhUUr0H4RcHRw7"
    }

def cache_output(path: str, filename_lambda, refresh: timedelta, returns_json = True, json_indent = 4):
    def decorator(func):
        @functools.wraps(func)
        def decorated_function(*args, **kwargs):
            filename = filename_lambda(*args, **kwargs)

            file_path = Path("cache/" + path + filename)

            # if data exists and was last updated within the refresh period, return it
            if file_path.is_file():
                with open("cache/" + path + filename, 'r') as f:
                    text = json.load(f)
                    
                    date = datetime.datetime.fromisoformat(text['timestamp']).date()

                    diff = datetime.datetime.now().date() - date

                    if diff < refresh:
                        return text['data']
            else:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            output = func(*args, **kwargs)
            with open("cache/" + path + filename, 'w') as f:
                f.write('{"timestamp": "' + str(datetime.datetime.now()) + '",\n "data": ' + (json.dumps(output, indent=json_indent) if returns_json else output)+ '}')
            return output

        return decorated_function
    return decorator

def get_event_alliance_pos(code: str):
    """ Returns a dict containing alliance numbers as keys and places as values """

    alliances = call("event/" + code + "/alliances")
    # print(alliances.json().keys())

    place_dict = {}

    if alliances is not None:
        for a in alliances:
            # print(a)
            status = a['status']

            match status['double_elim_round']:
                case 'Round 2':
                    place_dict[number_from_name(a['name'])] = 8
                case 'Round 3':
                    place_dict[number_from_name(a['name'])] = 6
                case 'Round 4':
                    place_dict[number_from_name(a['name'])] = 4
                case 'Round 5':
                    place_dict[number_from_name(a['name'])] = 3
                case 'Finals':
                    if status['status'] == 'won':
                        place_dict[number_from_name(a['name'])] = 1
                    else:
                        place_dict[number_from_name(a['name'])] = 2
        
        print(place_dict)
        print(len(place_dict.values()))
        if len(place_dict.values()) == 8:
            return place_dict          

def number_from_name(name: str) -> int:
    """ Converts an alliance "name" into its number 
    Ex "Alliance 8" -> 8 """

    num = int(name.strip("Alliance "))
    return num


def get_events(year: int):
    """ Returns all event codes from a given year """

    event_list = call("events/" + str(year) + "/keys")

    return event_list

"""  """
def perc_win(year: int):
    file_path = Path("cache/general/" + str(year) + "_alliance_percents.json")

    if file_path.is_file():
        with open("cache/general/" + str(year) + "_alliance_percents.json", 'r') as f:
            text = json.load(f)
            
            date = datetime.datetime.fromisoformat(text['timestamp']).date()

            diff = datetime.datetime.now().date() - date

            if diff < timedelta(hours=24):
                return text['data']

    places = {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: []}

    event_codes = get_events(year)

    for e in event_codes:
        print(e)
        pos = get_event_alliance_pos(e)

        if pos is not None:
            for i in range(1,9):
                places[pos[i]].append(i)

    the_stuff = {"places": {}, "alliances": {}}

    print(places)
    print ("PLACE STATS")
    for i in range(1,5):
        the_stuff['places'][i] = place_stats(i, places)
    # skip 5th and 7th
    the_stuff['places'][6] = place_stats(6, places)
    the_stuff['places'][8] = place_stats(8, places)

    print ("\nALLIANCE STATS")
    for i in range(1,9):
        the_stuff['alliances'][i] = alliance_place_stats(i, places)

    with open("cache/general/" + str(year) + "_alliance_percents.json", 'w') as f:
        f.write('{"timestamp": "' + str(datetime.datetime.now()) + '",\n "data": ' + json.dumps(the_stuff, indent=4) + '}')

    return the_stuff
        
def place_stats(place: int, places: dict):
    total = len(places[place])
    num = {}

    for i in range(1, 9):
        num[i] = places[place].count(i)

    num[0] = total

    perc = {}

    for i in num:
        perc[i] = num[i] / total
        
    print(place)
    print(total)
    print(num)
    print(perc)

    return num

def alliance_place_stats(alliance: int, places: dict):
    total = 0
    num = {}

    for i in range(1, 5):
        total += places[i].count(alliance)
        num[i] = places[i].count(alliance)

    total += places[6].count(alliance)
    num[6] = places[6].count(alliance)

    total += places[8].count(alliance)
    num[8] = places[8].count(alliance)

    num[0] = total

    perc = {}

    for i in num:
        perc[i] = num[i] / total

    print(alliance)
    print(total)
    print(num)
    print(perc)

    return num

def get_picks(code: str):
    alliances = call("event/" + code + "/alliances")

    all = {}

    if alliances is not None:
        for a in alliances:
            all[number_from_name(a['name'])] = a['picks']

    print(all)
        

def get_team_avg_pick(year: int, team_code: str):
    keys = call("team/" + team_code + "/events/keys")
    ev = 0
    num = 0

    for k in keys:
        print(k)
        alliance = call("team/" + team_code + "/event/" + k + "/status")
        event = call("event/" + k)
        
        if (not(event['week'] is None or event['year'] == 2020 or event['year'] == 2021)):
            ev += 1
            if alliance is None or alliance['alliance'] is None:
                num += 25
                print("25")
            else:
                pick = alliance['alliance']['pick']
                all_num = alliance['alliance']['number']
                val = pick * 8
                
                if (pick == 2):
                    val += 9 - all_num
                else:
                    val += all_num

                num += val
                print(val)

    print(ev)
    print(num)
    print(num / ev)

""" Finds all teams whose number is between min and max,
    exclusive, and participated in year_req """
@cache_output("general/teams/", lambda min, max, year: "teams_" + str(min) + "_to_" + str(max) + "_" + str(year) + ".json", timedelta(hours=24))
def get_team_avg_years_part(min: int, max: int, year_req: int):
    total_years = 0
    amt = 0
    team_data = {}

    for i in range(min, max):
        print(i)
        years = call("team/frc" + str(i) + "/years_participated")
        if years is not None:
            if year_req in years:
                total_years += len(years)
                amt += 1
                team_data[str(i)] = years

    print(total_years)
    print(amt)
    print(total_years / amt)
    print(team_data)

    output = {
        "total_years": total_years,
        "teams": amt,
        "avg": (total_years / amt),
        "team_data": team_data
    }

    return output

    # return json.loads("{'total_years': " + str(total_years) + ", 'teams': " + str(amt) + ", 'avg': " + str(total_years / amt) + ", 'team_data':" + str(team_data) + "}")



# get_team_avg_pick(2026, "frc2056")

# GEAR RATIO



# get_event_alliance_pos("2026tuis4")

# perc_win(2026)
# get_picks("2026mnum")

# for i in range(1, 9):
#     alliance_place_stats(i, data_apr_9)

print(get_team_avg_years_part(1, 1000, 2026))