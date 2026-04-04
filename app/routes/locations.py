from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from app.data import list_entities, get_entity, save_entity, delete_entity, slugify

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
    regions = sorted(set(l.get('region', '') for l in all_locs if l.get('region')))
    types = sorted(set(l.get('type', '') for l in all_locs if l.get('type')))
    return render_template('locations.html', locations=all_locs, campaign=campaign(),
                           regions=regions, types=types)

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
