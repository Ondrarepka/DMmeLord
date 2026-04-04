from flask import Blueprint, render_template, session, redirect, url_for

campaigns = Blueprint('campaigns', __name__, url_prefix='/c')

@campaigns.before_request
def require_campaign():
    if not session.get('campaign'):
        return redirect(url_for('main.index'))

@campaigns.route('/npcs')
def npcs():
    return render_template('npcs.html', campaign=session['campaign'])

@campaigns.route('/locations')
def locations():
    return render_template('locations.html', campaign=session['campaign'])

@campaigns.route('/sessions')
def sessions():
    return render_template('sessions.html', campaign=session['campaign'])

@campaigns.route('/economy')
def economy():
    return render_template('economy.html', campaign=session['campaign'])
