from flask import Blueprint, render_template, session, redirect, url_for, request
from app.data import list_entities
import os
import re

main = Blueprint('main', __name__)

CAMPAIGNS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'content', 'campaigns')

def get_campaigns():
    if not os.path.exists(CAMPAIGNS_DIR):
        return []
    return [d for d in os.listdir(CAMPAIGNS_DIR)
            if os.path.isdir(os.path.join(CAMPAIGNS_DIR, d))]

@main.route('/')
def index():
    campaigns = get_campaigns()
    if not session.get('campaign') and campaigns:
        session['campaign'] = campaigns[0]
    if not session.get('campaign'):
        return render_template('no_campaigns.html')
    return redirect(url_for('main.dashboard'))

@main.route('/dashboard')
def dashboard():
    camp = session.get('campaign')
    if not camp:
        return redirect(url_for('main.index'))

    all_npcs = list_entities(camp, 'npcs')
    all_locs = list_entities(camp, 'locations')
    all_sessions = list_entities(camp, 'sessions')
    all_sessions.sort(key=lambda s: s.get('number', 0), reverse=True)

    # Collect all active agreements across all NPCs
    urgent = []
    for npc in all_npcs:
        for agr in (npc.get('agreements') or []):
            d = agr.get('deadline_days', 0)
            if d:
                urgent.append({
                    'npc_name': npc['name'],
                    'npc_slug': npc['_slug'],
                    'text': agr['text'],
                    'days': d,
                })
    urgent.sort(key=lambda x: x['days'])

    return render_template('dashboard.html',
                           campaign=camp,
                           campaigns=get_campaigns(),
                           npc_count=len(all_npcs),
                           loc_count=len(all_locs),
                           session_count=len(all_sessions),
                           recent_sessions=all_sessions[:3],
                           urgent_agreements=urgent)

@main.route('/switch/<name>')
def switch_campaign(name):
    campaigns = get_campaigns()
    if name in campaigns:
        session['campaign'] = name
    return redirect(url_for('main.dashboard'))


@main.route('/search')
def search():
    camp = session.get('campaign')
    if not camp:
        return redirect(url_for('main.index'))
    q = request.args.get('q', '').strip()
    results = {'npcs': [], 'locations': [], 'sessions': []}
    if q:
        pat = re.compile(re.escape(q), re.IGNORECASE)
        def matches(entity, *fields):
            return any(pat.search(str(entity.get(f, '') or '')) for f in fields)

        for npc in list_entities(camp, 'npcs'):
            if matches(npc, 'name', 'role', 'faction', '_body'):
                results['npcs'].append(npc)
        for loc in list_entities(camp, 'locations'):
            if matches(loc, 'name', 'region', '_body'):
                results['locations'].append(loc)
        for s in list_entities(camp, 'sessions'):
            if matches(s, 'title', '_body'):
                results['sessions'].append(s)
        results['sessions'].sort(key=lambda s: s.get('number', 0), reverse=True)

    total = sum(len(v) for v in results.values())
    return render_template('search.html', q=q, results=results, total=total, campaign=camp)
