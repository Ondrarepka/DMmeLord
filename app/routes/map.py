import os
import uuid
from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from werkzeug.utils import secure_filename
from app.data import list_entities, get_campaign_config, save_campaign_config, campaign_dir

map_bp = Blueprint('map', __name__, url_prefix='/c/map')

ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'webp', 'gif'}


def campaign():
    return session.get('campaign')


def _map_static_dir(camp):
    """Return the static/maps/<campaign> dir, creating it if needed."""
    d = os.path.join(os.path.dirname(__file__), '..', 'static', 'maps', camp)
    os.makedirs(d, exist_ok=True)
    return d


@map_bp.before_request
def require_campaign():
    if not campaign():
        return redirect(url_for('main.index'))


@map_bp.route('/')
def index():
    camp = campaign()
    config = get_campaign_config(camp)
    map_cfg = config.get('map', {})
    all_locs = list_entities(camp, 'locations')
    pinned_slugs = {p['location_slug'] for p in map_cfg.get('pins', [])}
    unpinned_locs = [l for l in all_locs if l['_slug'] not in pinned_slugs]
    return render_template('map.html',
                           map_cfg=map_cfg,
                           all_locs=all_locs,
                           unpinned_locs=unpinned_locs,
                           campaign=camp)


@map_bp.route('/upload', methods=['POST'])
def upload():
    camp = campaign()
    f = request.files.get('map_image')
    if not f or not f.filename:
        return redirect(url_for('map.index'))
    ext = f.filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_EXT:
        return redirect(url_for('map.index'))
    filename = f'map_{camp}.{ext}'
    save_path = os.path.join(_map_static_dir(camp), filename)
    f.save(save_path)
    config = get_campaign_config(camp)
    config.setdefault('map', {})
    config['map']['image'] = f'maps/{camp}/{filename}'
    config['map'].setdefault('pins', [])
    save_campaign_config(camp, config)
    return redirect(url_for('map.index'))


@map_bp.route('/pin/add', methods=['POST'])
def add_pin():
    camp = campaign()
    data = request.get_json()
    config = get_campaign_config(camp)
    config.setdefault('map', {})
    pins = config['map'].setdefault('pins', [])
    pins.append({
        'id': str(uuid.uuid4())[:8],
        'x': round(float(data.get('x', 0)), 4),
        'y': round(float(data.get('y', 0)), 4),
        'location_slug': data.get('location_slug', ''),
        'location_name': data.get('location_name', ''),
    })
    save_campaign_config(camp, config)
    return jsonify({'ok': True})


@map_bp.route('/pin/<pin_id>/delete', methods=['POST'])
def delete_pin(pin_id):
    camp = campaign()
    config = get_campaign_config(camp)
    pins = config.get('map', {}).get('pins', [])
    config['map']['pins'] = [p for p in pins if p['id'] != pin_id]
    save_campaign_config(camp, config)
    return jsonify({'ok': True})


@map_bp.route('/clear', methods=['POST'])
def clear_image():
    camp = campaign()
    config = get_campaign_config(camp)
    config.setdefault('map', {})
    config['map']['image'] = ''
    save_campaign_config(camp, config)
    return redirect(url_for('map.index'))
