import os
import json
import uuid
import frontmatter
import markdown2
import re
import unicodedata
from datetime import date, timedelta

CONTENT_DIR = os.path.join(os.path.dirname(__file__), '..', 'content', 'campaigns')

def campaign_dir(campaign):
    return os.path.join(CONTENT_DIR, campaign)

def entity_dir(campaign, kind):
    return os.path.join(campaign_dir(campaign), kind)

def slugify(name):
    name = unicodedata.normalize('NFD', name)
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

# ── Generic file ops ──

def list_entities(campaign, kind):
    d = entity_dir(campaign, kind)
    if not os.path.exists(d):
        return []
    entities = []
    for f in sorted(os.listdir(d)):
        if f.endswith('.md'):
            post = frontmatter.load(os.path.join(d, f))
            data = dict(post.metadata)
            data['_slug'] = f[:-3]
            data['_body'] = post.content
            data['_body_html'] = markdown2.markdown(post.content, extras=['fenced-code-blocks', 'tables']) if post.content else ''
            entities.append(data)
    return entities

def get_entity(campaign, kind, slug):
    path = os.path.join(entity_dir(campaign, kind), f'{slug}.md')
    if not os.path.exists(path):
        return None
    post = frontmatter.load(path)
    data = dict(post.metadata)
    data['_slug'] = slug
    data['_body'] = post.content
    data['_body_html'] = markdown2.markdown(post.content, extras=['fenced-code-blocks', 'tables'])
    return data

def save_entity(campaign, kind, slug, metadata, body=''):
    d = entity_dir(campaign, kind)
    os.makedirs(d, exist_ok=True)
    post = frontmatter.Post(body, **metadata)
    path = os.path.join(d, f'{slug}.md')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(frontmatter.dumps(post))
    return slug

def delete_entity(campaign, kind, slug):
    path = os.path.join(entity_dir(campaign, kind), f'{slug}.md')
    if os.path.exists(path):
        os.remove(path)

# ── Campaign config (in-game calendar, real session log, trackers) ──

def _config_path(campaign):
    return os.path.join(campaign_dir(campaign), 'campaign.json')

def get_campaign_config(campaign):
    path = _config_path(campaign)
    if not os.path.exists(path):
        return {
            'ingame':        {'year': 912, 'month': 3, 'day': 16},
            'ingame_events': [],
            'real_events':   [],
            'trackers':      []
        }
    cfg = json.load(open(path, encoding='utf-8'))
    # migrations
    if 'calendar' in cfg and 'ingame' not in cfg:
        cfg['ingame'] = cfg.pop('calendar')
    if 'sessions' in cfg and 'ingame_events' not in cfg:
        cfg['ingame_events'] = cfg.pop('sessions')
    cfg.setdefault('ingame',        {'year': 912, 'month': 3, 'day': 16})
    cfg.setdefault('ingame_events', [])
    cfg.setdefault('real_events',   [])
    cfg.setdefault('trackers',      [])
    return cfg

def moon_phase(check_date):
    """Calculate moon phase for a given date. Returns dict with name, emoji, days_to_full."""
    known_new = date(2000, 1, 6)
    days = (check_date - known_new).days
    pos = days % 29.53059  # position in cycle 0–29.53
    full_pos = 14.765
    days_to_full = (full_pos - pos) if pos <= full_pos else (29.53059 - pos + full_pos)
    if   pos <  1.85: name, emoji = 'Nový měsíc',        '🌑'
    elif pos <  7.38: name, emoji = 'Dorůstající srpek',  '🌒'
    elif pos <  9.22: name, emoji = 'První čtvrt',        '🌓'
    elif pos < 14.77: name, emoji = 'Dorůstající měsíc',  '🌔'
    elif pos < 16.61: name, emoji = 'Úplněk',             '🌕'
    elif pos < 22.15: name, emoji = 'Ubývající měsíc',    '🌖'
    elif pos < 23.99: name, emoji = 'Poslední čtvrt',     '🌗'
    else:             name, emoji = 'Ubývající srpek',    '🌘'
    return {
        'name':         name,
        'emoji':        emoji,
        'days_to_full': round(days_to_full),
        'cycle_day':    round(pos),
        'illumination': round(abs(pos - full_pos) / full_pos * 100 if pos <= full_pos
                             else abs(29.53059 - pos + full_pos - full_pos) / full_pos * 100),
    }

def lunar_events_for_year(year):
    """
    Compute all full moons and new moons for a given year.
    Uses the same reference as moon_phase(). Accurate to ±1 day.
    Returns list of dicts: {day, month, year, type ('full_moon'|'new_moon'), emoji, label}
    """
    CYCLE = 29.53059
    HALF  = CYCLE / 2      # ~14.765 days new→full
    known_new = date(2000, 1, 6)

    # Find first new moon at or after Dec 1 of previous year
    start = date(year - 1, 12, 1)
    days_from_ref = (start - known_new).days
    pos = days_from_ref % CYCLE
    days_to_next_new = (CYCLE - pos) % CYCLE
    first_new = start + timedelta(days=round(days_to_next_new))

    events = []
    current_new = first_new
    while current_new.year <= year:
        full_moon_d = current_new + timedelta(days=round(HALF))
        for d, kind in [(current_new, 'new_moon'), (full_moon_d, 'full_moon')]:
            if d.year == year:
                events.append({
                    'day':   d.day,
                    'month': d.month,
                    'year':  d.year,
                    'type':  kind,
                    'emoji': '🌑' if kind == 'new_moon' else '🌕',
                    'label': 'Nový měsíc' if kind == 'new_moon' else 'Úplněk',
                    'auto':  True,
                })
        current_new += timedelta(days=round(CYCLE))

    return sorted(events, key=lambda e: (e['month'], e['day']))

def save_campaign_config(campaign, config):
    path = _config_path(campaign)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def advance_ingame(campaign, days):
    """Advance in-game calendar and decrement deadline trackers/agreements."""
    config = get_campaign_config(campaign)
    cal = config['ingame']
    d = date(cal['year'], cal['month'], cal['day']) + timedelta(days=days)
    config['ingame'] = {'year': d.year, 'month': d.month, 'day': d.day}
    for t in config.get('trackers', []):
        if t['type'] == 'countdown':
            t['value'] = max(0, t['value'] - days)
    save_campaign_config(campaign, config)
    # decrement NPC agreement deadlines
    for npc in list_entities(campaign, 'npcs'):
        agreements = npc.get('agreements') or []
        changed = False
        for agr in agreements:
            if agr.get('deadline_days'):
                agr['deadline_days'] = max(0, agr['deadline_days'] - days)
                changed = True
        if changed:
            meta = {k: v for k, v in npc.items() if not k.startswith('_')}
            meta['agreements'] = agreements
            save_entity(campaign, 'npcs', npc['_slug'], meta, npc.get('_body', ''))

# ── NPC helpers ──

DISPOSITIONS = ['neutral', 'allied', 'hostile', 'complicated', 'unknown']

def disposition_color(d):
    return {
        'allied':      'green',
        'neutral':     'blue',
        'hostile':     'red',
        'complicated': 'peach',
        'unknown':     'overlay',
    }.get(d, 'overlay')

# ── Wiki-link rendering ──

def apply_wiki_html(text, npc_map, loc_map):
    """Render markdown + resolve [[wiki links]] using pre-built name→slug maps."""
    if not text:
        return ''
    def replace_link(m):
        name = m.group(1).strip()
        if name in npc_map:
            return f'[{name}](/c/npcs/{npc_map[name]})'
        if name in loc_map:
            return f'[{name}](/c/locations/{loc_map[name]})'
        return f'**{name}**'
    text = re.sub(r'\[\[([^\]]+)\]\]', replace_link, text)
    return markdown2.markdown(text, extras=['fenced-code-blocks', 'tables'])

def render_wiki_html(campaign, text):
    """Convenience wrapper that builds maps itself (for single-entity detail pages)."""
    npcs = list_entities(campaign, 'npcs')
    locs = list_entities(campaign, 'locations')
    return apply_wiki_html(
        text,
        {n['name']: n['_slug'] for n in npcs},
        {l['name']: l['_slug'] for l in locs},
    )
