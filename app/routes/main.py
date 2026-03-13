from flask import Blueprint, render_template
from sqlalchemy import text

main = Blueprint('main', __name__)

@main.route('/regions')
def regions():
    from app import engine
    with engine.connect() as conn:
        result = conn.execute(text('SELECT nom_region FROM "ParcourStat".region ORDER BY nom_region'))
        regions = result.fetchall()
    return render_template('regions.html', regions=regions)
