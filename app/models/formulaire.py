from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, RadioField


class FiltreGraphique(FlaskForm):
    """
    La classe FiltreGraphique() définit le formulaire qui contient les filtres de sélection pour la page graphique
    
    Attributs : 
    formation_id : SelectField 
        Menu déroulant créé via la clé primaire des formations
        la valeur est convertie en int
    annee : SelectField
        Menu déroulant contenant l'année des données : 2018 et 2024
        La valeur est convertie en int
    situation : RadioField
        bouton de sélection pour choisir entre admis et candidats 
    submit : SubmitField 
        bouton de soumission du formulaire  
    """
    formation_id = SelectField('Formation', coerce=int)
    annee = SelectField('Année', coerce=int)
    situation = RadioField('Situation', choices=[('admis', 'Admis'), ('candidats', 'Candidats')])
    submit = SubmitField('Afficher')