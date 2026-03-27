def clean_arg(arg):
    """ 
    Nettoie les arguments : transforme une chaîne vide en None 
    """
    if arg == "":
        return None
    else:
        return arg