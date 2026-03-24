import os
import dotenv
from flask import Flask, render_template, request, redirect, url_for
from sqlalchemy import create_engine, text
from flask_login import current_user, login_required
from app.models.user import db, login, Favori

dotenv.load_dotenv(".env")

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'une-cle-secrete'
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'postgresql://{user}:{password}@{host}:{port}/{database}'.format(
        user=os.environ.get("pgUser"),
        password=os.environ.get("pgPassword"),
        host=os.environ.get("pgHost"),
        port=os.environ.get("pgPort"),
        database=os.environ.get("pgDatabase")
    )
)

# Initialisation
db.init_app(app)
login.init_app(app)
login.login_view = "auth.connexion"
login.login_message = "Veuillez vous connecter pour accéder à cette page."

with app.app_context():
    db.create_all()  # crée la table users si elle n'existe pas

# Connexion pour les requêtes manuelles
engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])

@app.route("/")
def index():
    with engine.connect() as conn:
        total_formations = conn.execute(text('SELECT COUNT(*) FROM "ParcourStat".formation')).scalar()
        total_etablissements = conn.execute(text('SELECT COUNT(*) FROM "ParcourStat".etablissement')).scalar()
        total_regions = conn.execute(text('SELECT COUNT(*) FROM "ParcourStat".region')).scalar()

    return render_template("index.html",
                           total_formations=total_formations,
                           total_etablissements=total_etablissements,
                           total_regions=total_regions)

@app.route("/formations")
def formations():
    selectivite = request.args.get("selectivite")
    recherche = request.args.get("recherche")
    page = request.args.get("page", 1, type=int)
    par_page = 50
    offset = (page - 1) * par_page

    conditions = []
    if selectivite == "true":
        conditions.append("f.selectivite = true")
    elif selectivite == "false":
        conditions.append("f.selectivite = false")
    if recherche:
        conditions.append(f"f.nom ILIKE '%{recherche}%'")

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    query = f'''
        SELECT f.id, f.nom, e.nom as etablissement, f.selectivite
        FROM "ParcourStat".formation f
        JOIN "ParcourStat".etablissement e ON f.etablissement_id = e.id
        {where}
        LIMIT {par_page} OFFSET {offset}
    '''

    count_query = f'''
        SELECT COUNT(*) FROM "ParcourStat".formation f
        {where}
    '''

    with engine.connect() as conn:
        result = conn.execute(text(query))
        formations = [dict(row._mapping) for row in result]
        total = conn.execute(text(count_query)).scalar()

    total_pages = (total // par_page) + 1

    return render_template("formations.html",
                           formations=formations,
                           page=page,
                           total_pages=total_pages,
                           selectivite=selectivite,
                           recherche=recherche)

@app.route("/formation/<int:id>")
def formation_detail(id):
    with engine.connect() as conn:
        result = conn.execute(text('''
            SELECT f.id, f.nom, f.selectivite, f.coordonnees_gps_formation,
                   e.nom as etablissement, e.statut, e.adresse, e.site_web,
                   t.nom as type_formation,
                   d.nom as discipline
            FROM "ParcourStat".formation f
            JOIN "ParcourStat".etablissement e ON f.etablissement_id = e.id
            JOIN "ParcourStat".types_formations t ON f.type_formation_id = t.id
            JOIN "ParcourStat".discipline d ON f.discipline_id = d.id
            WHERE f.id = :id
        '''), {"id": id})
        formation = dict(result.mappings().first())

    est_favori = False
    if current_user.is_authenticated:
        est_favori = Favori.query.filter_by(
            user_id=current_user.id,
            formation_id=id
        ).first() is not None

    return render_template("formation_detail.html",
                           formation=formation,
                           est_favori=est_favori)

@app.route("/favori/ajouter/<int:formation_id>")
@login_required
def ajouter_favori(formation_id):
    favori_existant = Favori.query.filter_by(
        user_id=current_user.id,
        formation_id=formation_id
    ).first()
    
    if not favori_existant:
        favori = Favori(user_id=current_user.id, formation_id=formation_id)
        db.session.add(favori)
        db.session.commit()
    
    return redirect(url_for("formation_detail", id=formation_id))


@app.route("/favori/supprimer/<int:formation_id>")
@login_required
def supprimer_favori(formation_id):
    favori = Favori.query.filter_by(
        user_id=current_user.id,
        formation_id=formation_id
    ).first()
    
    if favori:
        db.session.delete(favori)
        db.session.commit()
    
    return redirect(url_for("formation_detail", id=formation_id))

@app.route("/mes-favoris")
@login_required
def mes_favoris():
    favoris = Favori.query.filter_by(user_id=current_user.id).all()
    
    formations = []
    for favori in favoris:
        with engine.connect() as conn:
            result = conn.execute(text('''
                SELECT f.id, f.nom, e.nom as etablissement, f.selectivite
                FROM "ParcourStat".formation f
                JOIN "ParcourStat".etablissement e ON f.etablissement_id = e.id
                WHERE f.id = :id
            '''), {"id": favori.formation_id})
            formation = result.mappings().first()
            if formation:
                formations.append(dict(formation))
    
    return render_template("mes_favoris.html", formations=formations)




from app.routes.auth import auth
app.register_blueprint(auth)

from app.routes.main import main
app.register_blueprint(main)

from app.routes.graphique import graphique
app.register_blueprint(graphique)

if __name__ == "__main__":
    app.run(debug=True)

