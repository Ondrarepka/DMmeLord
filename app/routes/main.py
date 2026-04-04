from flask import Blueprint, render_template, session, redirect, url_for, request
import os

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
    campaign = session.get('campaign')
    if not campaign:
        return redirect(url_for('main.index'))
    return render_template('dashboard.html', campaign=campaign, campaigns=get_campaigns())

@main.route('/switch/<name>')
def switch_campaign(name):
    campaigns = get_campaigns()
    if name in campaigns:
        session['campaign'] = name
    return redirect(url_for('main.dashboard'))
