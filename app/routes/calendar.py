import uuid
from datetime import date as real_date
from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from app.data import (get_campaign_config, save_campaign_config,
                      advance_ingame, list_entities, moon_phase, lunar_events_for_year)

calendar = Blueprint('calendar', __name__, url_prefix='/c/calendar')

CZECH_MONTHS = [
    '', 'leden', 'únor', 'březen', 'duben', 'květen', 'červen',
    'červenec', 'srpen', 'září', 'říjen', 'listopad', 'prosinec'
]

REAL_EVENT_TYPES = {
    'full_moon':     {'label': 'Úplněk',          'emoji': '🌕'},
    'new_moon':      {'label': 'Nový měsíc',       'emoji': '🌑'},
    'eclipse_solar': {'label': 'Zatmění slunce',   'emoji': '☀️'},
    'eclipse_lunar': {'label': 'Zatmění měsíce',   'emoji': '🌑'},
    'custom':        {'label': 'Vlastní událost',  'emoji': '📅'},
}

INGAME_EVENT_TYPES = {
    'full_moon':     {'label': 'Úplněk',           'emoji': '🌕'},
    'new_moon':      {'label': 'Nový měsíc',        'emoji': '🌑'},
    'eclipse_solar': {'label': 'Zatmění slunce',    'emoji': '☀️'},
    'eclipse_lunar': {'label': 'Zatmění měsíce',    'emoji': '🌑'},
    'festival':      {'label': 'Svátek / festival', 'emoji': '🎉'},
    'note':          {'label': 'Poznámka',          'emoji': '📝'},
    'custom':        {'label': 'Vlastní událost',   'emoji': '📅'},
}


def campaign():
    return session.get('campaign')

@calendar.before_request
def require_campaign():
    if not campaign():
        return redirect(url_for('main.index'))

@calendar.route('/')
def index():
    config = get_campaign_config(campaign())
    cal = config['ingame']

    # NPC agreement deadlines
    deadlines = []
    for npc in list_entities(campaign(), 'npcs'):
        for agr in (npc.get('agreements') or []):
            if agr.get('deadline_days') is not None:
                deadlines.append({
                    'npc_name': npc['name'],
                    'npc_slug': npc['_slug'],
                    'text': agr['text'],
                    'days': agr['deadline_days'],
                })
    deadlines.sort(key=lambda x: x['days'])

    # Auto-computed lunar events for the in-game year
    ingame_year = cal['year']
    lunar_events = lunar_events_for_year(ingame_year)

    # Custom in-game events sorted by date
    def ingame_sort_key(e):
        return (e.get('year', 0), e.get('month', 0), e.get('day', 0))
    custom_events = sorted(config.get('ingame_events', []), key=ingame_sort_key, reverse=True)

    # Merge: auto lunar + custom, sorted for display
    all_ingame = sorted(
        lunar_events + custom_events,
        key=lambda e: (e.get('month', 0), e.get('day', 0)),
        reverse=True
    )

    # Real-world events sorted newest first
    real_events = sorted(config.get('real_events', []),
                         key=lambda e: e.get('date', ''), reverse=True)

    # Today's moon phase
    today = real_date.today()
    phase = moon_phase(today)

    return render_template('calendar.html',
                           cal=cal,
                           month_name=CZECH_MONTHS[cal['month']],
                           czech_months=CZECH_MONTHS[1:],
                           ingame_events=all_ingame,
                           custom_events=custom_events,
                           real_events=real_events,
                           real_event_types=REAL_EVENT_TYPES,
                           ingame_event_types=INGAME_EVENT_TYPES,
                           deadlines=deadlines,
                           trackers=config.get('trackers', []),
                           moon=phase,
                           today=today.isoformat(),
                           campaign=campaign())

# ── In-game calendar advance ──

@calendar.route('/advance', methods=['POST'])
def advance():
    days = int(request.form.get('days', 1) or 1)
    if days > 0:
        advance_ingame(campaign(), days)
    return redirect(url_for('calendar.index'))

# ── In-game events ──

@calendar.route('/ingame-event/add', methods=['POST'])
def ingame_event_add():
    config = get_campaign_config(campaign())
    day   = int(request.form.get('day',   1) or 1)
    month = int(request.form.get('month', 1) or 1)
    year  = int(request.form.get('year',  config['ingame']['year']) or config['ingame']['year'])
    title = request.form.get('title', '').strip()
    kind  = request.form.get('type', 'note')
    if title:
        config['ingame_events'].append({
            'id':    uuid.uuid4().hex[:8],
            'day':   day,
            'month': month,
            'year':  year,
            'type':  kind,
            'title': title,
        })
        save_campaign_config(campaign(), config)
    return redirect(url_for('calendar.index'))

@calendar.route('/ingame-event/<eid>/delete', methods=['POST'])
def ingame_event_delete(eid):
    config = get_campaign_config(campaign())
    config['ingame_events'] = [e for e in config['ingame_events'] if e['id'] != eid]
    save_campaign_config(campaign(), config)
    return redirect(url_for('calendar.index'))

# ── Real-world events ──

@calendar.route('/real-event/add', methods=['POST'])
def real_event_add():
    config = get_campaign_config(campaign())
    ev_date = request.form.get('date', '').strip()
    title   = request.form.get('title', '').strip()
    kind    = request.form.get('type', 'custom')
    if ev_date:
        config['real_events'].append({
            'id':    uuid.uuid4().hex[:8],
            'date':  ev_date,
            'type':  kind,
            'title': title,
        })
        save_campaign_config(campaign(), config)
    return redirect(url_for('calendar.index'))

@calendar.route('/real-event/<eid>/delete', methods=['POST'])
def real_event_delete(eid):
    config = get_campaign_config(campaign())
    config['real_events'] = [e for e in config['real_events'] if e['id'] != eid]
    save_campaign_config(campaign(), config)
    return redirect(url_for('calendar.index'))

# ── Trackers ──

@calendar.route('/tracker/add', methods=['POST'])
def tracker_add():
    config = get_campaign_config(campaign())
    kind = request.form.get('type', 'countdown')
    tracker = {
        'id':   uuid.uuid4().hex[:8],
        'name': request.form.get('name', '').strip(),
        'type': kind,
    }
    if kind == 'countdown':
        tracker['value'] = int(request.form.get('value', 0) or 0)
    elif kind == 'progress':
        tracker['current'] = int(request.form.get('current', 0) or 0)
        tracker['max']     = int(request.form.get('max', 5) or 5)
    elif kind == 'counter':
        tracker['value'] = int(request.form.get('value', 0) or 0)
    config['trackers'].append(tracker)
    save_campaign_config(campaign(), config)
    return redirect(url_for('calendar.index'))

@calendar.route('/tracker/<tid>/adjust', methods=['POST'])
def tracker_adjust(tid):
    config = get_campaign_config(campaign())
    delta = int(request.form.get('delta', 0))
    for t in config['trackers']:
        if t['id'] == tid:
            if t['type'] in ('countdown', 'counter'):
                t['value'] = max(0, t['value'] + delta)
            elif t['type'] == 'progress':
                t['current'] = max(0, min(t['max'], t['current'] + delta))
    save_campaign_config(campaign(), config)
    return jsonify({'ok': True})

@calendar.route('/tracker/<tid>/delete', methods=['POST'])
def tracker_delete(tid):
    config = get_campaign_config(campaign())
    config['trackers'] = [t for t in config['trackers'] if t['id'] != tid]
    save_campaign_config(campaign(), config)
    return redirect(url_for('calendar.index'))
