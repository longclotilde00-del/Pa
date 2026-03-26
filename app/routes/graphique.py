from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required
from app.models.user import db 
from app.models.parcourstat import Formation, Etablissement, Admissions, Candidatures
from sqlalchemy import func, or_, case, and_, not_
from app.models.formulaire import ChoixFormation
from app.utils.transformation import clean_arg

graphique = Blueprint('graphique', __name__)


#création de deux routes pour la page graphiques, une route /grphiques qui génère la structure de la page html avec la liste des formations, des établissements et les infos générales de la formation et retourne un fichier html
# graphiques_donnes retourne uniquement des données et des calculs de données avec les calculs de pourcentages etc.
#la mise en place de deux routes séparées permet de pouvoir racharger les graphqiues lorsqu'une nouvelle formation est choisie sans recharger entièrement la page
#création d'une route qui renvoie uniquement les données, pas de html. Elle sera appellée par fetch() dans le js du template

@graphique.route("/graphiques/donnees/<int:formation_id>/<int:annee>/<string:situation>", methods=['GET'])
@login_required
def graphiques_donnees(formation_id, annee, situation):    
    """
    Route permettant de retourner, pour chaque formation choisie, les données sous forme de pourcentages au format JSON pour les 4 graphiques : boursiers, sexe, filière d'origine, mention au bac.
    La route est appelée par fetch() dans le template html

    Paramètres GET : 
    formation_id, type=int : récupère l'identifiant de la formation choisie par l'utilisateur
    annee, type=int : récupère l'année des données choisie par l'utilisateur
    situation, type=str : récupère le choix entre admis et candidats

    """
    # si un des paramètres n'est pas choisi par l'utilisateur, js retourne un dictionnaire vide
    if not formation_id or not annee:
        return jsonify({})
    
    # on récupère ici d'abord la formation choisie via son id pour récupérer ensuite son nom
    formation_choisie = Formation.query.get(formation_id)
    if not formation_choisie:
        return jsonify({})

        # si l'utilisateur choisit la situation 'admis', sélection des données de la table admissions qui servent à remplir les 4 graphiques
    if situation == 'admis':
            # pour chaque colonne sélectionnée, on appelle la fonction sum() pour avoir la somme des données pour une formation choisie, peu importe son établissement
            # on définit également un alias pour chaque colonne avec label()
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
            func.avg(Admissions.ea_pc).label('capacite'), # utilisation de avg() ici puisque la données est déjà un pourcentage dans la table admission
            func.avg(Admissions.pa_f).label('femmes') # même chose ici, utilisation de avg()
        ).join(Formation).filter(
            Formation.nom == formation_choisie.nom, # ce filtre sélectionne toutes les formations ayant le même nom et permet de les agréger, peu importe l'établissement
            Admissions.annee == annee # filtre qui permet d'obtenir les données uniquement pour la date choisie par l'utilisateur 
        ).first() # une seule ligne de données retournée pour chaque requête
    else:
        #si l'utilisateur choisit une autre situation, c'est-à-dire 'candidats', sélecton des données de la tables candidatures
        stats = db.session.query(
            func.sum(Candidatures.et_c).label('total'),
            func.sum(Candidatures.ec_b_nb).label('boursiers'),
            func.sum(Candidatures.ec_nb_g).label('generale'),
            func.sum(Candidatures.ec_nb_t).label('techno'),
            func.sum(Candidatures.ec_nb_p).label('pro'),
            func.sum(Candidatures.et_cf).label('femmes'), # utilisation de sum() car il s'agit d'un chiffre brut dans la table candidatures, et non un pourcetage comme dans la table admissions
            db.literal(None).label('sans_mention'), #utilisation de db.literal(None) pour les colonnes suivantes car les données n'existent pas pour la table candidatures : les résultats du bac ne sont pas encore disponibles au moment des candidatures. On garde quand même les requêtes qui retournen None pour éviter les erreurs et garder la même structure. 
            db.literal(None).label('assez_bien'),
            db.literal(None).label('bien'),
            db.literal(None).label('tres_bien'),
            db.literal(None).label('capacite')
        ).join(Formation).filter(
                Formation.nom == formation_choisie.nom,
                Candidatures.annee == annee
        ).first() 
        

    # gestion des erreurs : si les données n'existent pas pour les paramètres sélectionnés par l'utilisateur, on retourne un dictionnaire vide
    if not stats or stats.total is None or stats.total == 0:
        return jsonify({})

    #éviter la division par 0 si le total est null ou 0
    total = stats.total

    def pct(val):
        """
        Cette fonction calcule un pourcentage de la valeur par rapport au total des admis et des candidats, 
        en fonction du choix de l'utilisateur, pour une formation choisie.
        La fonction retourne None si la valeur est absente ou si la valeur dépasse 100% pour éviter les erreurs.
        """
        if val is None or total == 0:
            return None
        result = round((val / total) * 100, 1)
        if result > 100:
            return None
        return result
    
    #le nombre de femmes est déjà un pourcentage dans la table admissions, mais c'est un chiffre brut dans la table candidatures. 
    # On crée donc ici un calcul de pourcentage selon la table qui est requêtée.
    pct_femmes = round(stats.femmes, 1) if situation == 'admis' else pct(stats.femmes)
       

    # On convertit ici le dictionnaire retourné en json, qui est ensuite récupéré par fetch() dans le javascript du template
    # le dictionnaire est utilisé ensuite pour remplir les 4 graphqiues et le résumé en bas de la page 
    # on retourne un dictionnaire en python, converti automatiquement json et apellé par fetch() dans le js
    #on retourne les données en pourcentages en appellant la fonction pct
    return jsonify({
        "pct_boursiers": pct(stats.boursiers), # pourcentage pour le graphique boursiers
        "pct_femmes": pct_femmes, # pourcentage pour le graphique sur le sexe
        "pct_techno": pct(stats.techno), # graphique sur la filière d'origine
        "pct_pro": pct(stats.pro),
        "pct_sm": pct(stats.sans_mention), # graphique sur la mention au bac
        "pct_ab": pct(stats.assez_bien),
        "pct_bien": pct(stats.bien),
        "pct_tb": pct(stats.tres_bien),
        "pct_generale": pct(stats.generale),
        "capacite": round(stats.capacite, 0) if stats.capacite is not None else None, # pour obtenir la capacité, moyenne des admis dans tous les établissements confondus pour une formation. Si la valeur est absente, retourne None
        "total": stats.total # nombre d'admis ou de candidats affiché dans le résumé
    })


#simplification de la route principale, qui fournit la liste des formation et l'année pour les filtres
#récupère les listes des formations pour que l'utilisateur puisse choisir 
#récupère les infos générales d'une formation : nom, établissement, sélectivité
#génère page html avec graphiques vides
@graphique.route("/graphiques", methods=['GET'])
@login_required
def graphiques():
    """
    Route qui permet d'afficher la page Graphiques de l'application, et qui retourne le template graphique.html avec le choix des formations, des années, établissements, et les infos générales sur chaque formation.
    Les données des quatre graphiques sont chargées via la route précédente /graphique/donnees

    """
    # on commence par récupérer la liste des formations par leur nom, peu importe leur établissement
    formations = db.session.query( 
        func.min(Formation.id).label('id'), #utilisation de min() pour avoir une liste de formation unique en sélectionnant un seul id pour plusieurs formations ayant le même nom
        Formation.nom
        ).filter(
            not_(Formation.nom.ilike('bac %')) #suppresion des formations dont le nom commencent par bac, car les différents bacs (S, ES, L...) sont présents dans les données, on ne veut garder que les formations d'enseignement supérieur
        ).group_by(Formation.nom).order_by(Formation.nom).all() #group by nom : regrouper les formations qui ont le même nom en une seule ligne

    
    # on instancie la classe ChoixFormation qui est un formulaire FlaskForm
    form = ChoixFormation()

    # remplissage dynamique du formulaire de choix de formation en récupérant le nom de la formation par son id
    # afin d'éviter un choix par défaut dans le formulaire, on met un "0"
    form.formation_id.choices = [(0, "Choisir une formation")] + [(f.id, f.nom) for f in formations] 
    # on définit les deux années que peut choisir l'utilisateur 
    form.annee.choices = [(2024, "2024"), (2018, "2018")]

    # récupération des paramètres donnés par l'utilisateur
    # on utilise clean_arg() afin de transformer les chaines vides en None et ainsi éviter le erreurs
    formation_id = clean_arg(request.args.get("formation_id", None))
    annee = request.args.get("annee", 0, type=int) 
    situation = request.args.get("situation", "admis")

    # on convertit l'identifiant de la formation en int
    formation_id = int(formation_id) if (formation_id and formation_id != 0) else None

    choix_annees = [(0, "Choisir une année")]

    #pré-remplissage du formulaire si l'id de la formation existe, garde en mémoire le champ sélectionné par l'utilisateur 
    if formation_id:
        form.formation_id.data = formation_id
        formation_nom = db.session.query(Formation.nom).filter(Formation.id == formation_id).scalar()
        q_adm = db.session.query(Admissions.annee).join(Formation).filter(Formation.nom == formation_nom)
        q_cand = db.session.query(Candidatures.annee).join(Formation).filter(Formation.nom == formation_nom)
        annees_db = [r[0] for r in q_adm.union(q_cand).order_by(Admissions.annee.desc()).all()]
        choix_annees += [(a, str(a)) for a in annees_db]

        # Si une seule année existe, on la force comme sélection par défaut
        if len(annees_db) == 1:
            annee_selectionnee = annees_db[0]
        # Sinon, si l'utilisateur n'a pas encore fait de choix manuel, on reste sur "0"
        elif annee_selectionnee not in annees_db:
            annee_selectionnee = 0
    else:
        # Si pas de formation, on peut proposer les deux par défaut ou rester vide
        choix_annees += [(2024, "2024"), (2018, "2018")]
        annee_selectionnee = 0

        form.annee.choices = choix_annees
        form.annee.data = annee
        form.situation.data = situation
    
    #si aucune formation n'est choisie, infos retourne None et la liste d'établissement retourne un dictionnaire vide
    infos = None
    etablissements = []
  

    # affichage des informtions générales sur les formations et les établsisements
    # Jointure entre formation et etablissement pour récupérer le nom de la formation, le nom de l'établissement et la sélectivité
    # si une formation est sélectionnée, on affiche la liste des établissements qui offrent cette formation, avec leurs infos: site web, adresse, nom 
    if formation_id:
        infos = Formation.query.get(formation_id)
        etablissements = db.session.query(
            Etablissement.nom,
            Etablissement.adresse,
            Etablissement.site_web,
            Admissions.ea_nb.label('nb_admis'),
            Candidatures.et_c.label('nb_candidats'),

            #Utilisation d'un case pour calculer le taux d'admission d'une formation choisie dans chaque établissement.
            #Si le nombre de candidats existe et est supérieur à 0, on divise le nombre d'admis par le nombre de candidats multiplié par 100
            #si le nombre de candidats n'existe pas, le calcul n'est pas effectué

            case(
        (Candidatures.et_c > 0, 
         func.round((Admissions.ea_nb.cast(db.Numeric) / Candidatures.et_c) * 100, 1)),
        else_=None
    ).label('taux_admission')
    #récupération des établissements
    ).join(Formation, Etablissement.id == Formation.etablissement_id)\
    .outerjoin(Admissions, and_(Admissions.formation_id == Formation.id, Admissions.annee == annee))\
    .outerjoin(Candidatures, and_(Candidatures.formation_id == Formation.id, Candidatures.annee == annee))\
    .filter(Formation.nom == infos.nom)\
    .order_by(Etablissement.nom).all()
        
    
    #génère page html avec les menus déoulants et les infos des formations seront chargées par fetch depuis le template html
    #les données pour les graphiques seront

    return render_template("graphique.html",
        form=form,
        formations=formations,
        annees=[2024, 2018],
        formation_id=formation_id,
        annee=annee,
        situation=situation,
        infos=infos,
        etablissements=etablissements,
        
    )