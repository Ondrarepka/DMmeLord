from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from app.data import list_entities, get_entity, save_entity, delete_entity, slugify, DISPOSITIONS, render_wiki_html, apply_wiki_html, get_campaign_config

npcs = Blueprint('npcs', __name__, url_prefix='/c/npcs')

def campaign():
    return session.get('campaign')

@npcs.before_request
def require_campaign():
    if not campaign():
        return redirect(url_for('main.index'))

@npcs.route('/')
def index():
    all_npcs = list_entities(campaign(), 'npcs')
    factions = sorted(set(n.get('faction', '') for n in all_npcs if n.get('faction')))
    all_locs = list_entities(campaign(), 'locations')
    loc_map  = {l['_slug']: l['name'] for l in all_locs}
    npc_name_map = {n['name']: n['_slug'] for n in all_npcs}
    loc_name_map = {l['name']: l['_slug'] for l in all_locs}
    for npc in all_npcs:
        npc['_body_html'] = apply_wiki_html(npc.get('_body', ''), npc_name_map, loc_name_map)
    locations_list = sorted(all_locs, key=lambda l: l['name'])
    ingame = get_campaign_config(campaign()).get('ingame', {'day': 1, 'month': 1, 'year': 912})
    return render_template('npcs.html', npcs=all_npcs, campaign=campaign(),
                           dispositions=DISPOSITIONS, factions=factions,
                           loc_map=loc_map, locations_list=locations_list,
                           ingame=ingame)

@npcs.route('/<slug>')
def detail(slug):
    npc = get_entity(campaign(), 'npcs', slug)
    if not npc:
        return redirect(url_for('npcs.index'))
    all_locs = list_entities(campaign(), 'locations')
    all_npcs = list_entities(campaign(), 'npcs')
    locations_list = sorted(all_locs, key=lambda l: l['name'])
    factions = sorted(set(n.get('faction', '') for n in all_npcs if n.get('faction')))
    npc['_body_html'] = render_wiki_html(campaign(), npc.get('_body', ''))
    ingame = get_campaign_config(campaign()).get('ingame', {'day': 1, 'month': 1, 'year': 912})
    return render_template('npc_detail.html', npc=npc,
                           dispositions=DISPOSITIONS,
                           locations_list=locations_list,
                           factions=factions,
                           ingame=ingame)


@npcs.route('/new', methods=['POST'])
def new():
    name = request.form.get('name', '').strip()
    if not name:
        return redirect(url_for('npcs.index'))
    slug = slugify(name)
    metadata = {
        'name': name,
        'role': request.form.get('role', ''),
        'location': request.form.get('location', ''),
        'faction': request.form.get('faction', ''),
        'disposition': request.form.get('disposition', 'unknown'),
        'last_meeting': request.form.get('last_meeting', ''),
        'last_meeting_summary': request.form.get('last_meeting_summary', ''),
        'agreements': [],
        'tags': [t.strip() for t in request.form.get('tags', '').split(',') if t.strip()],
    }
    save_entity(campaign(), 'npcs', slug, metadata)
    return redirect(url_for('npcs.index'))

@npcs.route('/<slug>/update', methods=['POST'])
def update(slug):
    npc = get_entity(campaign(), 'npcs', slug)
    if not npc:
        return jsonify({'error': 'not found'}), 404

    field = request.form.get('field')
    value = request.form.get('value', '')

    metadata = {k: v for k, v in npc.items() if not k.startswith('_')}

    if field == 'body':
        save_entity(campaign(), 'npcs', slug, metadata, value)
    elif field == 'tags':
        metadata['tags'] = [t.strip() for t in value.split(',') if t.strip()]
        save_entity(campaign(), 'npcs', slug, metadata, npc.get('_body', ''))
    elif field in metadata:
        metadata[field] = value
        save_entity(campaign(), 'npcs', slug, metadata, npc.get('_body', ''))

    return jsonify({'ok': True})

@npcs.route('/<slug>/agreement/add', methods=['POST'])
def add_agreement(slug):
    npc = get_entity(campaign(), 'npcs', slug)
    if not npc:
        return jsonify({'error': 'not found'}), 404
    metadata = {k: v for k, v in npc.items() if not k.startswith('_')}
    agreements = metadata.get('agreements') or []
    agreements.append({
        'text': request.form.get('text', ''),
        'deadline_days': int(request.form.get('deadline_days', 0) or 0),
    })
    metadata['agreements'] = agreements
    save_entity(campaign(), 'npcs', slug, metadata, npc.get('_body', ''))
    return jsonify({'ok': True})

@npcs.route('/<slug>/agreement/<int:idx>/delete', methods=['POST'])
def delete_agreement(slug, idx):
    npc = get_entity(campaign(), 'npcs', slug)
    if not npc:
        return jsonify({'error': 'not found'}), 404
    metadata = {k: v for k, v in npc.items() if not k.startswith('_')}
    agreements = metadata.get('agreements') or []
    if 0 <= idx < len(agreements):
        agreements.pop(idx)
    metadata['agreements'] = agreements
    save_entity(campaign(), 'npcs', slug, metadata, npc.get('_body', ''))
    return jsonify({'ok': True})

@npcs.route('/<slug>/delete', methods=['POST'])
def delete(slug):
    delete_entity(campaign(), 'npcs', slug)
    return redirect(url_for('npcs.index'))
