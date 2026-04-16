""" This file contains methods that obtain data from the TBA API """

import json
import datetime
from datetime import timedelta
from api_manager import call
from pathlib import Path
import functools

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

def add_bypass(endpoint: str):
    text = {}

    with open("cache/bypass.json", 'r') as f:
        text = json.load(f)

    if endpoint not in text['endpoints']:
        text['endpoints'].append(endpoint)

        with open("cache/bypass.json", 'w') as f:
            f.write(json.dumps(text, indent=4))

def is_real_event(event: dict):
    """ Returns whether the valid event passed in from call("event/code")
    has a week value associated with it, and is not from 2020 or 2021 """

    real = not(event['week'] is None or event['year'] == 2020 or event['year'] == 2021)
    if not real:
        add_bypass("event/" + event['key'])

    return real

def has_concluded(event: dict):
    """ Returns whether the current time is more than 24 hours after the event's end_date """

    end = datetime.datetime.fromisoformat(event['end_date']).date()
    diff = datetime.datetime.now().date() - end

    has_ended = diff > timedelta(hours=24)
    if has_ended:
        add_bypass("event/" + event['key'])
    
    return has_ended

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
        
# could be more robust by changing refresh time?
@cache_output("general/team/", lambda year, team: "team_" + team + "_avg_pick_" + year + ".json", timedelta(hours=24))
def get_team_avg_pick(year: int, team_code: str):
    keys = call("team/" + team_code + "/events/keys")
    ev = 0
    num = 0

    for k in keys:
        print(k)
        alliance = call("team/" + team_code + "/event/" + k + "/status")
        event = call("event/" + k)
        
        if is_real_event(event) and has_concluded(event):
            add_bypass("team/" + team_code + "/event/" + k + "/status")
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

    output = {
        "events": ev,
        "total_num": num,
        "avg": num / ev
    }

    print(output)

    return output


@cache_output("general/teams/", lambda min, max, year = 0: "teams_" + str(min) + "_to_" + str(max) + "_" + str(year) + ".json", timedelta(hours=24))
def get_team_avg_years_part(min: int, max: int, year_req = 0):
    """ Finds all teams whose number is between min and max,
    exclusive, and participated in year_req 
    if year_req == 0, find all teams that have participated in any season"""
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
            elif year_req == 0 and len(years) > 0:
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

@cache_output("general/team/", lambda team: "team_" + team + 'avg_quals.json', timedelta(hours=72))
def get_team_avg_qual_place(team_code: str):
    keys = call("team/" + team_code + "/events/keys")
    events = 0
    place = 0
    percs = 0
    total_teams = 0
    high = 1000000
    high_code = ""
    low = -1
    low_code = ""
    if (keys is not None):
        for k in keys:
            print(k)

            event = call("event/" + k)
            if is_real_event(event) and has_concluded(event):
                status = call("team/" + team_code + "/event/" + k + "/status")

                if status['qual'] is not None and status['qual']['ranking']['rank'] is not None:
                    events += 1

                    rank = status['qual']['ranking']['rank']
                    if rank > low:
                        low = rank
                        low_code = k
                    if rank < high:
                        high = rank
                        high_code = k

                    place += rank

                    teams = status['qual']['num_teams']
                    total_teams += teams

                    percs += rank / teams

        avg_place = place / events
        avg_perc = percs / events

        output = {
            "events": events,
            "avg_place": avg_place,
            "avg_perc": avg_perc,
            "total_teams": total_teams,
            "high": high,
            "high_code": high_code,
            "low": low,
            "low_code": low_code
        }

        return output
    
    return {"events": 0}
            

"""
"""
@cache_output("general/alliances/", lambda event: "pick_places_" + event + ".json", timedelta(hours=24))
def avg_pick_places(event_code: str):
    alliances = call("event/" + event_code + "/alliances")
    picks = {0: [], 1: [], 2: [], 3: []}
    # all_picks = {}
    pick_sums = {0: 0, 1: 0, 2: 0, 3: 0}
    total_sum = 0
    total_teams = 0

    low = -1
    lows = {0: -1, 1: -1, 2: -1, 3: -1}
    highs = {0: 1000000, 1: 1000000, 2: 1000000, 3: 1000000}

    high = 1000000
    # unreasonably high

    for i in alliances:
        for j in i['picks']:
            status = call("team/" + j + "/event/" + event_code + "/status")
            pick = status['alliance']['pick']
            rank = status['qual']['ranking']['rank']
            number = status['alliance']['number']

            picks[pick].append(rank)

            pick_sums[pick] += rank
            
            # all_picks[pick] = {"rank": rank, "number": number}

            total_sum += rank
            total_teams += 1


            if (rank > low):
                low = rank
            if (rank < high):
                high = rank

            if (rank > lows[pick]):
                lows[pick] = rank
            if (rank < highs[pick]):
                highs[pick] = rank

            print(rank)

    # print(all_picks)
    print(picks)
    print(pick_sums)

    pick_avg = {}

    for i in range(0, len(picks)):
        if len(picks[i]) > 0:
            avg = pick_sums[i] / len(picks[i])
            print(avg)
            pick_avg[i] = avg

    print("avg: " + str(total_sum / total_teams))

    # print(picks)

    output = {
        "high": high,
        "low": low,
        "highs": highs,
        "lows": lows,
        "total_avg": total_sum / total_teams,
        "total_sum": total_sum,
        "total_teams": total_teams,
        "pick_avg": pick_avg,
        "pick_sums": pick_sums,
        "picks": picks,
        # "all_picks": all_picks
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

# print(get_team_avg_years_part(1, 1000))
# print(avg_pick_places("2026alhu"))

time1 = datetime.datetime.now()
print(get_team_avg_qual_place("frc2056"))
time2 = datetime.datetime.now()
print(time1)
print(time2)
print(time1.date() - time2.date())
# add_bypass("team/frc3630")

# 2026-04-16 11:39:17.117560
# 2026-04-16 11:40:20.489354

# 2026-04-16 11:42:38.359329
# 2026-04-16 11:43:30.218613

# get_team_avg_pick(0, "frc2056")