from datetime import datetime, timezone, timedelta


def diff_ratings(
        old_time: datetime,
        old_total: int,
        old_members: list[tuple[str, int]],
        new_total: int,
        new_members: list[tuple[str, int]],
) -> str:
    """
    Returns a Discord markdown code block with a table formatted as in the provided example image.
    :param old_time: d
    :param old_total: prev clan total rating 24h ago
    :param old_members: prev list of (name, rating)
    :param new_total: clan total rating now
    :param new_members: list of (name, rating) now
    :returns: Markdown string for Discord
    """
    old_dict = dict(old_members)
    new_dict = dict(new_members)
    names = sorted(new_dict, key=lambda n: new_dict[n], reverse=True)

    # Calculate deltas
    table_entries = []
    for name in names:
        new = new_dict.get(name, 0)
        old = old_dict.get(name)
        delta = None
        if old is not None:
            delta = new - old
        else:
            delta = new
        table_entries.append((name, new, delta))

    # Add leavers at the end
    leavers = [(name, old_dict[name], -old_dict[name]) for name in old_dict if name not in new_dict]
    table_entries += leavers

    # Split into columns for Discord code block
    # 3 columns: name | rating | delta
    max_name = max((len(name) for name, _, _ in table_entries))
    max_rating = max((len(str(rt)) for _, rt, _ in table_entries))
    max_delta = max((len(f"{d}") for _, _, d in table_entries))

    lines = []
    for entry in table_entries:
        name, rating, delta = entry
        name_fmt = f"{name:<{max_name}}"
        rating_fmt = f"{rating:>{max_rating}}"
        # Color code for Discord: green for >0, red for <0, grey for 0
        if delta > 0:
            delta_fmt = f"+{delta}"
        elif delta < 0:
            delta_fmt = f"{delta}"
        else:
            continue
        delta_fmt = f"{delta_fmt:>{max_delta + 2}}"
        lines.append(f"{name_fmt} {rating_fmt} {delta_fmt}")

    # Compose header
    clan_name = "AFI"
    session_delta = new_total - (old_total or 0)
    date = f"**{datetime.now(timezone(timedelta(hours=3))).strftime("%H:%M %d.%m.%Y")}**"
    # Compose the bold header line
    header = f"**C {old_time.strftime("%H:%M")} полк {clan_name} набрал {session_delta} очков.**"
    # Compose session stats and position
    stats = f"У полка {new_total} ({new_total - old_total}) очков."

    # Discord block with all
    result = (
            f"{date}\n"
            f"{header}\n"
            f"{stats}\n"
            f"```\n"
            + "\n".join(lines)[0:1500] +
            "\n```"
    )
    return result
