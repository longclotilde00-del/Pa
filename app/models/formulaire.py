from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField

class ChoixFormation(FlaskForm):
    # On crée un menu déroulant (SelectField)
    formation_id = SelectField('Formation', coerce=int)
    annee = SelectField('Année', coerce=int)
    situation = SelectField('Situation', choices=[('admis', 'Admis'), ('candidats', 'Candidats')])
    submit = SubmitField('Afficher')