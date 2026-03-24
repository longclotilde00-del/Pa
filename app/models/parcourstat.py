from app.models.user import db

class Region(db.Model):
    __tablename__ = 'region'
    __table_args__ = {"schema": "ParcourStat"}

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.Text)

class Academie(db.Model):
    __tablename__ = 'academie'
    __table_args__ = {"schema": "ParcourStat"}

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.Text)
    region_id = db.Column(db.Integer, db.ForeignKey('ParcourStat.region.id'))

class Departement(db.Model):
    __tablename__ = 'departement'
    __table_args__ = {"schema": "ParcourStat"}

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.Text)
    academie_id = db.Column(db.Integer, db.ForeignKey('ParcourStat.academie.id'))

class Commune(db.Model):
    __tablename__ = 'commune'
    __table_args__ = {"schema": "ParcourStat"}

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.Text)
    departement_id = db.Column(db.Integer, db.ForeignKey('ParcourStat.departement.id'))

class TypeFormation(db.Model):
    __tablename__ = 'types_formations'
    __table_args__ = {"schema": "ParcourStat"}

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.Text)

class Discipline(db.Model):
    __tablename__ = 'discipline'
    __table_args__ = {"schema": "ParcourStat"}

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.Text)
    type = db.Column(db.Integer, db.ForeignKey('ParcourStat.types_formations.id'))

class Etablissement(db.Model):
    __tablename__ = 'etablissement'
    __table_args__ = {"schema": "ParcourStat"}

    id = db.Column(db.Text, primary_key=True)
    nom = db.Column(db.Text)
    statut = db.Column(db.Text)
    site_web = db.Column(db.Text)
    adresse = db.Column(db.Text)
    nombre_etudiants = db.Column(db.Integer)
    url_logo = db.Column(db.Text)
    url_image = db.Column(db.Text)
    commune_id = db.Column(db.Integer, db.ForeignKey('ParcourStat.commune.id'))
    academie_id = db.Column(db.Integer, db.ForeignKey('ParcourStat.academie.id'))

class Formation(db.Model):
    __tablename__ = 'formation'
    __table_args__ = {"schema": "ParcourStat"}

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.Text, nullable=False)
    etablissement_id = db.Column(db.Text, db.ForeignKey('ParcourStat.etablissement.id'), nullable=False)
    type_formation_id = db.Column(db.Integer, db.ForeignKey('ParcourStat.types_formations.id'), nullable=False)
    discipline_id = db.Column(db.Integer, db.ForeignKey('ParcourStat.discipline.id'), nullable=False)
    selectivite = db.Column(db.Boolean)
    coordonnees_gps_formation = db.Column(db.Text)
    identifiant_parcoursup = db.Column(db.Text)

class Candidatures(db.Model):
    __tablename__ = 'candidatures'
    __table_args__ = (
        db.UniqueConstraint('formation_id', 'annee', name='candidatures_unique'), #ajout de db.UniqueConstraint pour éviter d'avoir deux fois la même formation pour la même année
        {"schema": "ParcourStat"}
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    formation_id = db.Column(db.Integer, db.ForeignKey('ParcourStat.formation.id'), nullable=False)
    annee = db.Column(db.Integer, nullable=False)
    et_c = db.Column(db.Integer)  
    et_cf = db.Column(db.Integer)     
    et_c_pp = db.Column(db.Integer)   
    ec_i = db.Column(db.Integer)   
    ec_nb_g = db.Column(db.Integer)   
    ec_b_nb_g = db.Column(db.Integer) 
    ec_nb_t = db.Column(db.Integer)  
    ec_b_nb_t = db.Column(db.Integer) 
    ec_nb_p = db.Column(db.Integer)  
    ec_b_nb = db.Column(db.Integer)   
    ec_ac = db.Column(db.Integer)     
    etc_pc = db.Column(db.Integer)
    ec_nb_g_pc = db.Column(db.Integer)
    ec_nb_t_pc = db.Column(db.Integer)
    ec_nb_p_pc = db.Column(db.Integer)
    eac_pc = db.Column(db.Integer)
    etc_ce = db.Column(db.Integer)
    ec_ce_pc = db.Column(db.Integer)
    etc_r_pa = db.Column(db.Integer)
    etc_a_pe = db.Column(db.Integer)
    etc_f_a_pe = db.Column(db.Integer)
    ec_tg_pa_e = db.Column(db.Integer)
    ec_b_tg_pa_e = db.Column(db.Integer)
    ec_tt_pa_e = db.Column(db.Integer)
    ec_b_tt_pa_e = db.Column(db.Integer)
    ec_tp_pa_e = db.Column(db.Integer)
    ec_b_tp_pa_e = db.Column(db.Integer)
    eac_pa_e = db.Column(db.Integer)


class Admissions(db.Model):
    __tablename__ = 'admissions'
    __table_args__ = (
        db.UniqueConstraint('formation_id', 'annee', name='admissions_unique'), 
        {"schema": "ParcourStat"}
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    formation_id = db.Column(db.Integer, db.ForeignKey('ParcourStat.formation.id'), nullable=False)
    annee = db.Column(db.Integer, nullable=False)
    ea_pc = db.Column(db.Integer)     
    ea_i = db.Column(db.Integer)
    ea_bn_b = db.Column(db.Integer)   
    ea_nb = db.Column(db.Integer)    
    ea_nb_g = db.Column(db.Integer)   
    ea_nb_t = db.Column(db.Integer)   
    ea_nb_p = db.Column(db.Integer)   
    ea_ac = db.Column(db.Integer)
    ea_nb_si = db.Column(db.Integer)
    ea_nb_sm = db.Column(db.Integer)
    ea_nb_ab = db.Column(db.Integer)  
    ea_nb_b = db.Column(db.Integer)   
    ea_nb_tb = db.Column(db.Integer)
    ea_nb_tbf = db.Column(db.Integer) 
    ea_nb_g_m = db.Column(db.Integer)
    ea_nb_t_m = db.Column(db.Integer)
    ea_nb_p_m = db.Column(db.Integer)
    ea_nb_ime = db.Column(db.Integer)
    ea_f_ime = db.Column(db.Integer)
    ea_ima = db.Column(db.Integer)
    ea_ima_pcv = db.Column(db.Integer)
    pa_ab = db.Column(db.Integer)
    pa_af_pp = db.Column(db.Integer)
    pa_f = db.Column(db.Integer)
    pa_nb_ima = db.Column(db.Integer)
    pa_nb_ima_pcv = db.Column(db.Integer)
    pa_nb_ime = db.Column(db.Integer)
    pa_nb_b = db.Column(db.Integer)
    pa_nb = db.Column(db.Integer)
    pa_nb_si_mb = db.Column(db.Integer)
    pa_nb_sm = db.Column(db.Integer)
    pa_nb_ab = db.Column(db.Integer)
    pa_nb_b_mb = db.Column(db.Integer)
    pa_nb_tb = db.Column(db.Integer)
    pa_nb_tb_f = db.Column(db.Integer)
    pa_nb_g = db.Column(db.Integer)
    pa_m_bg = db.Column(db.Integer)
    pa_nb_t = db.Column(db.Integer)
    pa_m_bt = db.Column(db.Integer)
    pa_nb_p = db.Column(db.Integer)
    pa_m_bp = db.Column(db.Integer)



# Relations
etablissement = db.relationship('Etablissement', backref='formations')
type_formation = db.relationship('TypeFormation', backref='formations')
discipline = db.relationship('Discipline', backref='formations')
formation = db.relationship('Formation', backref='candidatures')
formation = db.relationship('Formation', backref='admissions')
