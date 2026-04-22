from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from app.data import list_entities, get_entity, save_entity, delete_entity, render_wiki_html
from datetime import date

sessions_bp = Blueprint('sessions', __name__, url_prefix='/c/sessions')


def campaign():
    return session.get('campaign')


@sessions_bp.before_request
def require_campaign():
    if not campaign():
        return redirect(url_for('main.index'))


@sessions_bp.route('/')
def index():
    all_sessions = list_entities(campaign(), 'sessions')
    all_sessions.sort(key=lambda s: s.get('number', 0), reverse=True)
    return render_template('sessions.html', sessions=all_sessions,
                           campaign=campaign(), today=str(date.today()))


@sessions_bp.route('/new', methods=['POST'])
def new():
    all_sessions = list_entities(campaign(), 'sessions')
    next_num = max((s.get('number', 0) for s in all_sessions), default=0) + 1
    title = request.form.get('title', '').strip() or f'Session {next_num}'
    session_date = request.form.get('date', '') or str(date.today())
    slug = f'session-{next_num:03d}'
    metadata = {
        'number': next_num,
        'title': title,
        'date': session_date,
        'location': '',
        'npcs': [],
    }
    save_entity(campaign(), 'sessions', slug, metadata, '')
    return redirect(url_for('sessions.detail', slug=slug))


@sessions_bp.route('/<slug>')
def detail(slug):
    s = get_entity(campaign(), 'sessions', slug)
    if not s:
        return redirect(url_for('sessions.index'))
    s['_body_html'] = render_wiki_html(campaign(), s.get('_body', ''))
    all_npcs = list_entities(campaign(), 'npcs')
    all_locs = list_entities(campaign(), 'locations')
    session_npcs_names = s.get('npcs') or []
    session_npc_objs = [n for n in all_npcs if n['name'] in session_npcs_names]
    remaining_npcs = [n for n in all_npcs if n['name'] not in session_npcs_names]
    return render_template('session_detail.html', s=s, campaign=campaign(),
                           all_npcs=all_npcs, all_locs=all_locs,
                           session_npc_objs=session_npc_objs,
                           remaining_npcs=remaining_npcs)


@sessions_bp.route('/<slug>/update', methods=['POST'])
def update(slug):
    s = get_entity(campaign(), 'sessions', slug)
    if not s:
        return jsonify({'error': 'not found'}), 404
    field = request.form.get('field')
    value = request.form.get('value', '')
    metadata = {k: v for k, v in s.items() if not k.startswith('_')}
    if field == 'body':
        save_entity(campaign(), 'sessions', slug, metadata, value)
    elif field == 'number':
        metadata['number'] = int(value) if value else 0
        save_entity(campaign(), 'sessions', slug, metadata, s.get('_body', ''))
    elif field == 'location':
        metadata['location'] = value
        save_entity(campaign(), 'sessions', slug, metadata, s.get('_body', ''))
    elif field in metadata:
        metadata[field] = value
        save_entity(campaign(), 'sessions', slug, metadata, s.get('_body', ''))
    return jsonify({'ok': True})


@sessions_bp.route('/<slug>/npc/add', methods=['POST'])
def add_npc(slug):
    s = get_entity(campaign(), 'sessions', slug)
    if not s:
        return jsonify({'error': 'not found'}), 404
    metadata = {k: v for k, v in s.items() if not k.startswith('_')}
    npcs = list(metadata.get('npcs') or [])
    name = request.form.get('name', '').strip()
    if name and name not in npcs:
        npcs.append(name)
    metadata['npcs'] = npcs
    save_entity(campaign(), 'sessions', slug, metadata, s.get('_body', ''))
    return jsonify({'ok': True})


@sessions_bp.route('/<slug>/npc/remove', methods=['POST'])
def remove_npc(slug):
    s = get_entity(campaign(), 'sessions', slug)
    if not s:
        return jsonify({'error': 'not found'}), 404
    metadata = {k: v for k, v in s.items() if not k.startswith('_')}
    npcs = list(metadata.get('npcs') or [])
    name = request.form.get('name', '').strip()
    if name in npcs:
        npcs.remove(name)
    metadata['npcs'] = npcs
    save_entity(campaign(), 'sessions', slug, metadata, s.get('_body', ''))
    return jsonify({'ok': True})


@sessions_bp.route('/<slug>/delete', methods=['POST'])
def delete(slug):
    delete_entity(campaign(), 'sessions', slug)
    return redirect(url_for('sessions.index'))
