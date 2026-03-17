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


#deuxième essai d'une route avec claude mais en suivant le TD du prof
#création d'une route qui renvoie uniquement les données, pas de html. Elle sera appellée par fetch() dans le js du template

@app.route("/graphiques/donnees", methods=['GET'])
@login_required
def graphiques_donnees():
    #récupération des paramètres envoyés par l'URL via les choix de l'utilisateur
    formation_id = request.args.get('formation_id', type=int)
    annee = request.args.get('annee', type=int)
    situation = request.args.get('situation', 'admis') #si admis n'a pas été choisi, candidat sera utilisé automatiquement

    #si l'utilisateur oublie de sélectionner un filtre, js retourne un dictionnaire vide
    if not formation_id or not annee:
        return {}

    with engine.connect() as conn: #on connecte la base de données PostgreSQL pour ce bloc de code
        #si l'utilisateur choisit admis sélection de la table admissions
        if situation == 'admis':
            #sélection des colonnes de la table admissions qui nous servirons pour les 4 graphiques
            # Pour les admis
            # on veut les statistiques générales pour uen formation choisie peu importe son établissement
            # somme des lignes pour uen formation, puis calcul d'un pourcentage du total des lignes agrégées
            stats = conn.execute(text("""
            SELECT
                SUM(a.ea_nb)    AS total,
                SUM(a.ea_bn_b)  AS boursiers,
                SUM(a.ea_nb_g)  AS generale,
                SUM(a.ea_nb_t)  AS techno,
                SUM(a.ea_nb_p)  AS pro,
                SUM(a.ea_nb_sm) AS sans_mention,
                SUM(a.ea_nb_ab) AS assez_bien,
                SUM(a.ea_nb_b)  AS bien,
                SUM(a.ea_nb_tb) AS tres_bien,
                AVG(a.ea_pc)    AS capacite, --déjà un pourcetage
                AVG(a.pa_f)     AS femmes    --déjà un pourcentage
            FROM "ParcourStat".admissions a
            JOIN "ParcourStat".formation f ON a.formation_id = f.id
            WHERE f.nom = (SELECT nom FROM "ParcourStat".formation WHERE id = :fid LIMIT 1)
            AND a.annee = :annee
        """), {"fid": formation_id, "annee": annee}).fetchone()

            #sinon, sélection de la table candidatures
        else:
            # Pour les candidats
            stats = conn.execute(text("""
                SELECT
                    SUM(c.et_c)    AS total,
                    SUM(c.ec_b_nb) AS boursiers,
                    SUM(c.ec_nb_g) AS generale,
                    SUM(c.ec_nb_t) AS techno,
                    SUM(c.ec_nb_p) AS pro,
                    NULL           AS sans_mention,
                    NULL           AS assez_bien,
                    NULL           AS bien,
                    NULL           AS tres_bien,
                    NULL           AS capacite,
                    SUM(c.et_cf)   AS femmes
                FROM "ParcourStat".candidatures c
                JOIN "ParcourStat".formation f ON c.formation_id = f.id
                WHERE f.nom = (SELECT nom FROM "ParcourStat".formation WHERE id = :fid LIMIT 1)
                AND c.annee = :annee
            """), {"fid": formation_id, "annee": annee}).fetchone() #utilisation de fecthone() au lieu de fetchall() puisqu'on veut un seul résultat, il existe en effet qu'une seule ligne par formation et par année dans les tables admissions et candaidatures 

    #gestion des erreurs
    #si pas de données pour la requête sélectionnée, retourne un dictionnaire vide
    if not stats:
        return {}

    #éviter la division par 0 si el total est null ou 0
    total = stats.total or 1

    #fonction qui calcule un pourcentage, retourne none si la valeur est absente
    def pct(val):
        if val is None or total == 0:
            return None
        return round((val / total) * 100, 1)
    
    #le nombre de femmes est déjà un pourcentage dans la table admissions, mais c'est un chiffre brut dans la table candidatures. 
    # On crée donc ici un calcul de pourcentage selon la table qui est requêtée.
    if situation == 'admis':
        pct_femmes = round(stats.femmes, 1) if stats.femmes is not None else None
    else:
        pct_femmes = pct(stats.femmes)  # et_cf est un nombre brut → division par total


    #on retourne un dictionnaire en python, converti automatiquement json et apellé par fetch() dans le js
    #on retourne les données en pourcentages en appellant la fonction pct
    return {
        "pct_boursiers": pct(stats.boursiers),
        "pct_femmes": pct_femmes,        
        "pct_techno": pct(stats.techno),
        "pct_pro": pct(stats.pro),
        "pct_sm": pct(stats.sans_mention),
        "pct_ab": pct(stats.assez_bien),
        "pct_bien": pct(stats.bien),
        "pct_tb": pct(stats.tres_bien),
        "pct_generale": pct(stats.generale),
        "capacite": round(stats.capacite, 0) if stats.capacite is not None else None, #on fait une moyenne de la capacité d'une formation dans les établissements en FRance 
        "total": stats.total
    }


#simplification de la route principale, qui fournit la liste des formation et l'année pour les filtres
#récupère les listes des formations pour que l'utilisateur puisse choisir 
#récupère les infos générales d'une formation : nom, établissement, sélectivité
#génère page html avec graphiques vides
@app.route("/graphiques", methods=['GET'])
@login_required
def graphiques():
    #MIN(id) et MIN(etablissement_id) pour éviter les doublons quand plusieurs lignes ont le même nom de formation 
    #group by nom : regrouper les formations qui ont le même nom en une seule ligne
    #mappings : accéder aux colonnes par leur nom dans le template
    formations = db.session.execute(text("""
        SELECT MIN(id) as "id", nom, MIN(etablissement_id) as "etablissement_id" 
        FROM "ParcourStat".formation
        GROUP BY nom
        ORDER BY nom
    """)).mappings().fetchall()

#récupération des paramètres sélectionnés par l'utilisateur
    formation_id = request.args.get('formation_id', type=int)
    situation = request.args.get('situation', 'admis')

    
#si une formation est sélectionnée, on récupère les données issues des années disponibles en base pour cette même formation
    if formation_id:
        annees = db.session.execute(text("""
            SELECT DISTINCT annee FROM "ParcourStat".candidatures WHERE formation_id = :fid
            UNION
            SELECT DISTINCT annee FROM "ParcourStat".admissions WHERE formation_id = :fid
            ORDER BY annee DESC
        """), {"fid": formation_id}).fetchall()
        annees = [r[0] for r in annees]
    #si aucune formation sélectionnée, affiche les années disponibles
    else:
        annees = db.session.execute(text("""
            SELECT DISTINCT annee FROM "ParcourStat".candidatures
            UNION
            SELECT DISTINCT annee FROM "ParcourStat".admissions
            ORDER BY annee DESC
        """)).fetchall()
        annees = [r[0] for r in annees]

#récupère année sélectionnée par l'utilisateur. si aucune année sélectionnée, on prend la première par défaut A CHANGER
    annee = request.args.get('annee', type=int, default=annees[0] if annees else None)

    # Infos générales uniquement, pas les stats
    #Jointure entre formation et etablissement pour récupérer
    # le nom de la formation, le nom de l'établissement et la sélectivité
    infos = None
    if formation_id:
        with engine.connect() as conn:
            infos = conn.execute(text("""
                SELECT f.nom, e.nom AS etablissement, f.selectivite
                FROM "ParcourStat".formation f
                JOIN "ParcourStat".etablissement e ON f.etablissement_id = e.id
                WHERE f.id = :fid
            """), {"fid": formation_id}).fetchone()
    
    # si une formaion est sélectionné, on affiche la liste des établissements qui offrent cette formation
    etablissements = []
    if formation_id:
        with engine.connect() as conn:
            etablissements = conn.execute(text("""
                SELECT DISTINCT e.nom, e.adresse, e.site_web
                FROM "ParcourStat".formation f
                JOIN "ParcourStat".etablissement e ON f.etablissement_id = e.id
                WHERE f.nom = (SELECT nom FROM "ParcourStat".formation WHERE id = :fid LIMIT 1)
                ORDER BY e.nom
            """), {"fid": formation_id}).mappings().fetchall()
    
    #génère page html avec les menus déoulants et les infos des formations seront chargées par fetch depuis le template html
    #les données pour les graphiques seront

    return render_template("graphique.html",
        formations=formations,
        annees=annees,
        formation_id=formation_id,
        annee=annee,
        situation=situation,
        infos=infos,
        etablissements=etablissements
    )


from app.routes.auth import auth
app.register_blueprint(auth)

from app.routes.main import main
app.register_blueprint(main)

if __name__ == "__main__":
    app.run(debug=True)

