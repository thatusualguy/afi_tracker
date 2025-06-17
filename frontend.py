from datetime import datetime

import discord

from config import TIMEZONE


def get_member_delta(old_members: list[tuple[str, int]], new_members: list[tuple[str, int]]):
    old_dict = dict(old_members)
    new_dict = dict(new_members)
    names = sorted(new_dict, key=lambda n: new_dict[n], reverse=True)

    table_entries = []
    for name in names:
        new = new_dict.get(name, 0)
        old = old_dict.get(name)
        delta = None
        if old is not None:
            delta = new - old
        else:
            delta = new

        if delta != 0:
            table_entries.append((name, new, delta))

    leavers = [(name, old_dict[name], -old_dict[name]) for name in old_dict if name not in new_dict]
    table_entries += leavers
    return table_entries


def generate_report(old_time: datetime,
                    old_total: int,
                    old_members: list[tuple[str, int]],
                    new_total: int,
                    new_members: list[tuple[str, int]],
                    ) -> discord.Embed:
    now = datetime.now(TIMEZONE)
    title = f"**{now:%H:%M %d.%m.%Y}**"

    member_20 = new_members[19]

    description = (f"С {old_time} полк набрал {new_total - old_total} очков.\n"
                   f"Всего у полка {new_total} очков.\n"
                   f"Конец топ-20 = {member_20[1]}.")

    member_delta = get_member_delta(old_members, new_members)[:50]
    items_names = [str(x[0]) for x in member_delta]
    field_names = "```\n" + "\n".join(items_names) + "```"

    items_ratings = [str(x[1]) for x in member_delta]
    field_ratings = "```\n" + "\n".join(items_ratings) + "```"

    items_diffs = []
    for diff in [x[2] for x in member_delta]:
        if diff > 0:
            # Green background
            items_diffs.append(f"\u001b[2;32m+{diff}\u001b[0m")
        elif diff < 0:
            # Red background
            items_diffs.append(f"\u001b[2;31m{diff}\u001b[0m")
        else:
            items_diffs.append(f"{diff}")
    field_diffs = "```ansi\n" + "\n".join(items_diffs) + "```"

    embed = discord.Embed(
        title=title,
        description=description,
    )
    for field in [field_names, field_ratings, field_diffs]:
        embed.add_field(
            name=" ",
            inline=True,
            value=field,
        )

    return embed
