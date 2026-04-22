from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
import os
from app.data import render_wiki_html

lore_bp = Blueprint('lore', __name__, url_prefix='/c/lore')

LORE_PAGES = {
    'encounters': 'Setkání na cestách',
    'gods':       'Bohové a víra',
}

CONTENT_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'content', 'campaigns')

def campaign():
    return session.get('campaign')

@lore_bp.before_request
def require_campaign():
    if not campaign():
        return redirect(url_for('main.index'))

def _lore_path(camp, slug):
    d = os.path.join(CONTENT_DIR, camp, 'lore')
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f'{slug}.md')

def _read(camp, slug):
    p = _lore_path(camp, slug)
    if not os.path.exists(p):
        return ''
    with open(p, 'r', encoding='utf-8') as f:
        return f.read()

def _write(camp, slug, content):
    with open(_lore_path(camp, slug), 'w', encoding='utf-8') as f:
        f.write(content)

@lore_bp.route('/')
def index():
    return redirect(url_for('lore.page', slug='encounters'))

@lore_bp.route('/<slug>')
def page(slug):
    if slug not in LORE_PAGES:
        return redirect(url_for('lore.index'))
    content = _read(campaign(), slug)
    html = render_wiki_html(campaign(), content) if content else ''
    return render_template('lore.html', slug=slug, title=LORE_PAGES[slug],
                           content=content, html=html, pages=LORE_PAGES,
                           campaign=campaign())

@lore_bp.route('/<slug>/save', methods=['POST'])
def save(slug):
    if slug not in LORE_PAGES:
        return jsonify({'error': 'not found'}), 404
    _write(campaign(), slug, request.form.get('content', ''))
    return jsonify({'ok': True})
