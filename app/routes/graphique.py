from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required
from app.models.user import db 
from app.models.parcourstat import Formation, Etablissement, Admissions, Candidatures
from sqlalchemy import func, or_, case

graphique = Blueprint('graphique', __name__)


#création de deux routes pour la page graphiques, une route /grphiques qui génère la structure de la page html avec la liste des formations, des établissements et les infos générales de la formation et retourne un fichier html
# graphiques_donnes retourne uniquement des données et des calculs de données avec les calculs de pourcentages etc.
#la mise en place de deux routes séparées permet de pouvoir racharger les graphqiues lorsqu'une nouvelle formation est choisie sans recharger entièrement la page
#création d'une route qui renvoie uniquement les données, pas de html. Elle sera appellée par fetch() dans le js du template

@graphique.route("/graphiques/donnees", methods=['GET'])
@login_required
def graphiques_donnees():
    #récupération des paramètres envoyés par l'URL via les choix de l'utilisateur
    formation_id = request.args.get('formation_id', type=int)
    annee = request.args.get('annee', type=int)
    situation = request.args.get('situation', 'admis') #si admis n'a pas été choisi, candidat sera utilisé automatiquement

    #si l'utilisateur oublie de sélectionner un filtre, js retourne un dictionnaire vide
    if not formation_id or not annee:
        return jsonify({})
    
    #on récupère ici d'abord la formation choisie via son id pour récupérer ensuite son nom
    formation_choisie = Formation.query.get(formation_id)
    if not formation_choisie:
        return jsonify({})

        #si l'utilisateur choisit admis sélection de la table admissions
    if situation == 'admis':
            #sélection des colonnes de la table admissions qui nous servirons pour les 4 graphiques
            # Pour les admis
            # on veut les statistiques générales pour uen formation choisie peu importe son établissement
            # somme des lignes pour uen formation, puis calcul d'un pourcentage du total des lignes agrégées
            #on agrège ici les formations ayant le même nom pour l'année choisie
        stats = db.session.query(
            func.sum(Admissions.ea_nb).label('total'),
            func.sum(Admissions.ea_bn_b).label('boursiers'),
            func.sum(Admissions.ea_nb_g).label('generale'),
            func.sum(Admissions.ea_nb_t).label('techno'),
            func.sum(Admissions.ea_nb_p).label('pro'),
            func.sum(Admissions.ea_nb_sm).label('sans_mention'),
            func.sum(Admissions.ea_nb_ab).label('assez_bien'),
            func.sum(Admissions.ea_nb_b).label('bien'),
            func.sum(Admissions.ea_nb_tb).label('tres_bien'),
            func.avg(Admissions.ea_pc).label('capacite'),
            func.avg(Admissions.pa_f).label('femmes') # Déjà un % dans la table admission
        ).join(Formation).filter(
            Formation.nom == formation_choisie.nom,
            Admissions.annee == annee
        ).first()
    else:
        # Pour les candidats
        stats = db.session.query(
            func.sum(Candidatures.et_c).label('total'),
            func.sum(Candidatures.ec_b_nb).label('boursiers'),
            func.sum(Candidatures.ec_nb_g).label('generale'),
            func.sum(Candidatures.ec_nb_t).label('techno'),
            func.sum(Candidatures.ec_nb_p).label('pro'),
            func.sum(Candidatures.et_cf).label('femmes'), # Chiffre brut dans la table candidatures
            db.literal(None).label('sans_mention'),
            db.literal(None).label('assez_bien'),
            db.literal(None).label('bien'),
            db.literal(None).label('tres_bien'),
            db.literal(None).label('capacite')
        ).join(Formation).filter(
                Formation.nom == formation_choisie.nom,
                Candidatures.annee == annee
        ).first()
        

    #gestion des erreurs
    #si pas de données pour la requête sélectionnée, retourne un dictionnaire vide
    if not stats or stats.total is None or stats.total == 0:
        return jsonify({})

    #éviter la division par 0 si el total est null ou 0
    total = stats.total

    #fonction qui calcule un pourcentage, retourne none si la valeur est absente
    def pct(val):
        if val is None or total == 0:
            return None
        result = round((val / total) * 100, 1)
        if result > 100:
            return None
        return result
    
    #le nombre de femmes est déjà un pourcentage dans la table admissions, mais c'est un chiffre brut dans la table candidatures. 
    # On crée donc ici un calcul de pourcentage selon la table qui est requêtée.
    pct_femmes = round(stats.femmes, 1) if situation == 'admis' else pct(stats.femmes)
       

    #on retourne un dictionnaire en python, converti automatiquement json et apellé par fetch() dans le js
    #on retourne les données en pourcentages en appellant la fonction pct
    return jsonify({
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
    })


#simplification de la route principale, qui fournit la liste des formation et l'année pour les filtres
#récupère les listes des formations pour que l'utilisateur puisse choisir 
#récupère les infos générales d'une formation : nom, établissement, sélectivité
#génère page html avec graphiques vides
@graphique.route("/graphiques", methods=['GET'])
@login_required
def graphiques():
    #MIN(id) et MIN(etablissement_id) pour éviter les doublons quand plusieurs lignes ont le même nom de formation 
    #group by nom : regrouper les formations qui ont le même nom en une seule ligne
    #mappings : accéder aux colonnes par leur nom dans le template
    formations = db.session.query(
        func.min(Formation.id).label('id'),
        Formation.nom
        ).filter(
            ~Formation.nom.ilike('bac %') #suppresion des formations dont le nom commencent par bac, car les différents bacs (S, ES, L...) sont présents dans les données
        ).group_by(Formation.nom).order_by(Formation.nom).all()
    
    #récupération des paramètres sélectionnés par l'utilisateur
    formation_id = request.args.get('formation_id', type=int)
    situation = request.args.get('situation', 'admis')

    
#si une formation est sélectionnée, on récupère les données issues des années disponibles en base pour cette même formation
    if formation_id:
        formation_nom = db.session.query(Formation.nom).filter(Formation.id == formation_id).scalar()
        requete_admissions = db.session.query(Admissions.annee).join(Formation).filter(Formation.nom == formation_nom)
        requete_candidats = db.session.query(Candidatures.annee).join(Formation).filter(Formation.nom == formation_nom)
        annees_res = requete_admissions.union(requete_candidats).order_by(Admissions.annee.desc()).all()
    
    #si aucune formation sélectionnée, affiche les années disponibles
    else:
        annees_res = db.session.query(Admissions.annee).distinct().order_by(Admissions.annee.desc()).all()
        
    annees = [r[0] for r in annees_res]

    #récupère année sélectionnée par l'utilisateur. si aucune année sélectionnée, on prend la première par défaut A CHANGER
    annee = request.args.get('annee', type=int, default=annees[0] if annees else None)

    infos = None
    etablissements = []
  

    # Infos générales uniquement, pas les stats
    #Jointure entre formation et etablissement pour récupérer
    # le nom de la formation, le nom de l'établissement et la sélectivité
        # si une formaion est sélectionné, on affiche la liste des établissements qui offrent cette formation, avec leurs infos: site web, adresse, nom 
    # on effectue un case dans la requête sql pour afficher le taux d'admission de la formation dans chaque établissement : si le nombre de candidats existe, et donc est supérieur à 0, on divise le nombre d'admis par le nombre de candidats et on multiplie par 100
    if formation_id:
        infos = Formation.query.get(formation_id)
        etablissements = db.session.query(
            Etablissement.nom,
            Etablissement.adresse,
            Etablissement.site_web,
            Admissions.ea_nb.label('nb_admis'),
            Candidatures.et_c.label('nb_candidats'),
            #calcul du taux d'admission avec un case
            case(
        (Candidatures.et_c > 0, 
         func.round((Admissions.ea_nb.cast(db.Numeric) / Candidatures.et_c) * 100, 1)),
        else_=None
    ).label('taux_admission')
).join(Formation, Etablissement.id == Formation.etablissement_id)\
 .outerjoin(Admissions, (Admissions.formation_id == Formation.id) & (Admissions.annee == annee))\
 .outerjoin(Candidatures, (Candidatures.formation_id == Formation.id) & (Candidatures.annee == annee))\
 .filter(Formation.nom == infos.nom)\
 .order_by(Etablissement.nom).all()
        
    
    #génère page html avec les menus déoulants et les infos des formations seront chargées par fetch depuis le template html
    #les données pour les graphiques seront

    return render_template("graphique.html",
        formations=formations,
        annees=annees,
        formation_id=formation_id,
        annee=annee,
        situation=situation,
        infos=infos,
        etablissements=etablissements,
        
    )