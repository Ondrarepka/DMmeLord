from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from app.data import list_entities, get_entity, save_entity, delete_entity, slugify, render_wiki_html, apply_wiki_html

locations = Blueprint('locations', __name__, url_prefix='/c/locations')

def campaign():
    return session.get('campaign')

@locations.before_request
def require_campaign():
    if not campaign():
        return redirect(url_for('main.index'))

@locations.route('/')
def index():
    all_locs = list_entities(campaign(), 'locations')
    all_npcs = list_entities(campaign(), 'npcs')
    npc_map  = {n['name']: n['_slug'] for n in all_npcs}
    loc_map  = {l['name']: l['_slug'] for l in all_locs}
    for loc in all_locs:
        loc['_body_html'] = apply_wiki_html(loc.get('_body', ''), npc_map, loc_map)
    regions = sorted(set(l.get('region', '') for l in all_locs if l.get('region')))
    types = sorted(set(l.get('type', '') for l in all_locs if l.get('type')))
    return render_template('locations.html', locations=all_locs, campaign=campaign(),
                           regions=regions, types=types)

@locations.route('/<slug>')
def detail(slug):
    loc = get_entity(campaign(), 'locations', slug)
    if not loc:
        return redirect(url_for('locations.index'))
    all_npcs = list_entities(campaign(), 'npcs')
    all_sessions = list_entities(campaign(), 'sessions')
    loc_npcs = [n for n in all_npcs if n.get('location') == loc.get('name')]
    loc_sessions = sorted(
        [s for s in all_sessions if s.get('location') == loc.get('name')],
        key=lambda s: s.get('number', 0), reverse=True
    )
    all_locs = list_entities(campaign(), 'locations')
    types   = sorted(set(l.get('type', '')   for l in all_locs if l.get('type')))
    regions = sorted(set(l.get('region', '') for l in all_locs if l.get('region')))
    loc['_body_html'] = render_wiki_html(campaign(), loc.get('_body', ''))
    return render_template('location_detail.html', loc=loc,
                           loc_npcs=loc_npcs, loc_sessions=loc_sessions,
                           types=types, regions=regions)


@locations.route('/new', methods=['POST'])
def new():
    name = request.form.get('name', '').strip()
    if not name:
        return redirect(url_for('locations.index'))
    slug = slugify(name)
    metadata = {
        'name': name,
        'type': request.form.get('type', ''),
        'region': request.form.get('region', ''),
        'tags': [t.strip() for t in request.form.get('tags', '').split(',') if t.strip()],
    }
    save_entity(campaign(), 'locations', slug, metadata)
    return redirect(url_for('locations.index'))

@locations.route('/<slug>/update', methods=['POST'])
def update(slug):
    loc = get_entity(campaign(), 'locations', slug)
    if not loc:
        return jsonify({'error': 'not found'}), 404
    field = request.form.get('field')
    value = request.form.get('value', '')
    metadata = {k: v for k, v in loc.items() if not k.startswith('_')}
    if field == 'body':
        save_entity(campaign(), 'locations', slug, metadata, value)
    elif field == 'tags':
        metadata['tags'] = [t.strip() for t in value.split(',') if t.strip()]
        save_entity(campaign(), 'locations', slug, metadata, loc.get('_body', ''))
    elif field in metadata:
        metadata[field] = value
        save_entity(campaign(), 'locations', slug, metadata, loc.get('_body', ''))
    return jsonify({'ok': True})

@locations.route('/<slug>/delete', methods=['POST'])
def delete(slug):
    delete_entity(campaign(), 'locations', slug)
    return redirect(url_for('locations.index'))
