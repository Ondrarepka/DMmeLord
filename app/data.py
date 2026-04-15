import os
import frontmatter
import markdown2
import re
from datetime import date


CONTENT_DIR = os.path.join(os.path.dirname(__file__), '..', 'content', 'campaigns')

def campaign_dir(campaign):
    return os.path.join(CONTENT_DIR, campaign)

def entity_dir(campaign, kind):
    return os.path.join(campaign_dir(campaign), kind)

def slugify(name):
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

def render_wiki_html(campaign, text):
    """Render markdown with [[wiki links]] resolved to entity detail pages."""
    if not text:
        return ''
    npcs = list_entities(campaign, 'npcs')
    locs = list_entities(campaign, 'locations')
    npc_map  = {n['name']: n['_slug'] for n in npcs}
    loc_map  = {l['name']: l['_slug'] for l in locs}

    def replace_link(m):
        name = m.group(1).strip()
        if name in npc_map:
            return f'[{name}](/c/npcs/{npc_map[name]})'
        if name in loc_map:
            return f'[{name}](/c/locations/{loc_map[name]})'
        return f'**{name}**'

    text = re.sub(r'\[\[([^\]]+)\]\]', replace_link, text)
    return markdown2.markdown(text, extras=['fenced-code-blocks', 'tables'])
