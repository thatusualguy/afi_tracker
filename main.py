from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

def get_ratings(clan_name: str) -> tuple[int, list[tuple[str, int]]]:
    url = f"https://warthunder.com/en/community/claninfo/{quote(clan_name)}"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "lxml")

    # общий рейтинг клана
    total_rating_tag = soup.select("div.squadrons-counter__value")[0]
    total_rating: int = int(total_rating_tag.text.strip())

    # рейтинг участников с их именами, сортированный
    members = soup.select("div.squadrons-members__grid-item")

    names = map(lambda member: member.text.strip(), members[7::6])
    ratings = map(lambda member: int(member.text.strip()), members[8::6])

    result = list(zip(names, ratings))
    result.sort(key=lambda member: member[1], reverse=True)

    return total_rating, result

clan = "Anthems For Insubordinates"
result = get_ratings(clan)
print(result)
