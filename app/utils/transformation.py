#à mettre dans un fichier utils/transformation.py puis l'importer dans ce fichier
def clean_arg(arg):
    """ Nettoie les arguments : transforme une chaîne vide en None """
    if arg == "":
        return None
    else:
        return arg