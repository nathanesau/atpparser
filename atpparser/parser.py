from bs4 import BeautifulSoup
from urllib.request import urlopen, Request
import math
from atpparser.constants import HEADERS
from atpparser.util import format_player_name, get_archive_url, get_archive_filename, \
    get_draw_url, get_draw_filename

# downloads archive to "archive_{year}.html"
def downloadArchive(year):
    archive_url = get_archive_url(year)
    archive_filename = get_archive_filename(year)
    req = Request(url=archive_url, headers=HEADERS)
    html = urlopen(req).read()

    # write html content to file
    html_file = open(archive_filename, "w")
    html_file.write(html.decode("utf-8"))
    html_file.close()
    return archive_filename

# return list of draws:
# [{"title": "Brisbane", "link": "/en/scores/archive/brisbane"}]
def parseArchive(html_file):
    
    def strip(title_tag):
        title = str(title_tag.contents)
        for substr in ["  ", '\\n', '\\', '[', ']', '\'', '\"']:
            title = title.replace(substr, '')
        return title

    data = []

    soup = BeautifulSoup(open(html_file), "html.parser")
    for tourney in soup.find_all('tr', {'class': 'tourney-result'}):
        try: # this parsing method works for 2019, 2018, ...
            title_tag = tourney.find_all('span', {'class': 'tourney-title'})
            title = strip(title_tag[0])
            links = tourney.find_all('a')
            for link in links: # only some links are relevant
                href = None if 'href' not in link.attrs else link['href']
                if href is not None and "singles" in href:
                    data.append({"title": title, "link": href})
        except: # this parsing method works for 2020
            title_tag = tourney.find_next('a')
            title = strip(title_tag)
            links = tourney.find_all('a')
            for link in links: # only some links are relevant
                href = None if 'href' not in link.attrs else link['href']
                if href is not None and "singles" in href:
                    data.append({"title": title, "link": href})
    return data

# downloads draw to "{draw_title}_{draw_year}.html"
def downloadDraw(draw_title, draw_link, draw_year):
    draw_url = get_draw_url(draw_link)
    draw_filename = get_draw_filename(draw_title, draw_year)
    req = Request(url=draw_url, headers=HEADERS)
    html = urlopen(req).read()

     # write html content to file
    html_file = open(draw_filename, "w")
    html_file.write(html.decode("utf-8"))
    html_file.close()
    return draw_filename

def parseDraw(draw_file):

    def get_winner(pair, roundNum, numWinsDict):
        player1 = pair[0]
        player2 = pair[1]
        num_wins1 = 0 if player1 not in numWinsDict else numWinsDict[player1]
        num_wins2 = 0 if player2 not in numWinsDict else numWinsDict[player2]
        return player1 if num_wins1 >= roundNum else player2 if num_wins2 >= roundNum else "unknown"

    player_finalRound = {}
    player_result = {}
    seedDict = {} # key: player, value: seed
    countryDict = {} # key: player, value: country_image
    numWinsDict = {} # key: player, value: numWins
    round1_players = []
    win_players = []

    soup = BeautifulSoup(open(draw_file), "html.parser")

    # dates
    date_tag = soup.find_all('span', {'class': 'tourney-dates'})[0]
    dates = date_tag.text.strip().replace('\n', '').replace(' - ', ' ').split(' ')

    # players, matchups
    for box in soup.find_all('div', {'class': 'scores-draw-entry-box'}):
        table_tags = box.find_all('table')
        if len(table_tags) > 0:  # round 1 entry
            tr_tags = box.find_all('tr')
            for tr_tag in tr_tags:
                span_tags = tr_tag.find_all('span')
                a_tags = tr_tag.find_all('a')
                if len(a_tags) > 0:  # player info exists
                    playerName = a_tags[0]['data-ga-label']
                    img_tags = tr_tag.find_all('img')
                    if len(img_tags) > 0:
                        playerCountry = img_tags[0]['src']
                        countryDict[playerName] = playerCountry
                    round1_players.append(playerName)
                else:
                    playerName = "bye"
                    playerCountry = ""
                    countryDict[playerName] = playerCountry
                    round1_players.append(playerName)
                if len(span_tags) > 0:
                    seed = span_tags[0]
                    if seed:
                        seed_str = str(seed).strip()
                        for substr in ['\n', '\t', '<', '>', 'span', '\\', '/', '(', ')']:
                            seed_str = seed_str.replace(substr, '')
                        seedDict[playerName] = seed_str
        else:  # round 2, 3, ..., entry
            a_tags = box.find_all('a')
            if len(a_tags) > 0:  # only true if match has happened
                playerName = a_tags[0]['data-ga-label']
                win_players.append(playerName)
            else:
                playerName = "unknown"
                win_players.append(playerName)

    drawSize = len(round1_players)
    if not (drawSize == 8 or drawSize == 16 or drawSize == 32 or \
            drawSize == 64 or drawSize == 128):
        print("cannot convert HTML to db (drawSize = ", drawSize, ")")
        return # parser was not programmed to handle this case
    
    numRounds = int(math.log(drawSize)/math.log(2)) + 1
    rounds = [[] for i in range(numRounds)]

    for i in range(0, drawSize, 2):  # round1
        rounds[0].append((round1_players[i], round1_players[i+1]))

    for player in round1_players:  # numWinsDict
        numWinsDict[player] = win_players.count(player)

    num_players_this_round = drawSize
    for roundNum in range(1, numRounds, 1):  # round2, ...
        num_players_this_round = int(num_players_this_round / 2)
        if num_players_this_round > 1:
            for i in range(0, num_players_this_round, 2):
                w1 = get_winner(rounds[roundNum-1][i], roundNum, numWinsDict)
                w2 = get_winner(rounds[roundNum-1][i+1], roundNum, numWinsDict)
                rounds[roundNum].append((w1, w2))
        else:  # last round
            w = get_winner(rounds[roundNum-1][0], roundNum, numWinsDict)
            rounds[roundNum].append((w))

    def find_winner(player1, player2, roundNum):
        if roundNum == numRounds - 1:
            return None # last round, don't look for winner

        if roundNum == numRounds - 2:
            return rounds[roundNum+1][0]

        for matchup in rounds[roundNum+1]:
            if player1 in matchup[0] or player1 in matchup[1]:
                return player1
            elif player2 in matchup[0] or player2 in matchup[1]:
                return player2
        
        return None

    matchupList = []
    for roundNum in range(0, numRounds, 1): # fill matchupList
        if roundNum != (numRounds - 1):
            for i in range(0, len(rounds[roundNum]), 1):
                player1 = rounds[roundNum][i][0]
                player2 = rounds[roundNum][i][1]
                winner = find_winner(player1, player2, roundNum)                
                matchup = {"round": roundNum+1, "player1": format_player_name(player1),
                    "player2": format_player_name(player2), "winner": format_player_name(winner)}
                matchupList.append(matchup)
                player_finalRound[player1] = roundNum + 1
                player_finalRound[player2] = roundNum + 1
        else:  # final round
            player1 = rounds[roundNum][0]
            player2 = ""
            winner = None
            matchup = {"round": roundNum+1, "player1": format_player_name(player1),
                "player2": format_player_name(player2), "winner": format_player_name(winner)}
            matchupList.append(matchup)
            player_finalRound[player1] = roundNum + 1

    # determine player result
    # let X = final round
    # let N = num rounds
    # let x = N - X + 1
    # then result = 2 ^ (x-1) + 1
    for player_name, final_round in player_finalRound.items():
        x = numRounds - final_round
        result = 1 if x == 0 else 2 ** (x - 1) + 1
        player_result[player_name] = result

    playerList = []
    for player in round1_players:
        seed = "0" if player not in seedDict else seedDict[player]
        seed = seed.strip()
        countryIcon = "" if player not in countryDict else countryDict[player]
        countryCode = countryIcon[-7:].replace(".svg", "")
        playerList.append({"name": format_player_name(player), "seed": seed,
            "countryCode": countryCode, "result": player_result[player]})

    return {"dates": {"start": dates[0], "end": dates[1]},
        "matchups": matchupList, "players": playerList}