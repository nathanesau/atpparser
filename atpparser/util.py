from atpparser.constants import ARCHIVE_URL, BASE_URL
import tempfile

# remove apostrophe from player name
def format_player_name(player_name):
    if not player_name:
        return None

    return player_name.replace("'", "")

def get_archive_url(year):
    return "{archive_url}?year={year}".format(
        archive_url=ARCHIVE_URL, year=year
    )

# filename to download archive to
def get_archive_filename(year):
    return "{tmp}/archive_{year}.html".format(
        tmp=tempfile.gettempdir(), year=year
    )

def get_draw_url(link):
    return "{base_url}{link}".format(
        base_url=BASE_URL, link=link)

# filename to download draw to
def get_draw_filename(tournament, year):
    return "{tmp}/{tournament}_{year}.html".format(
        tmp=tempfile.gettempdir(), tournament=tournament, year=year
    )