// Initialisation de la recherche dans le menu déroulant des formations
// on récupère l'id définit dans le template graphique.html pour les formations pour récupérer la liste
const selectFormation = document.getElementById('formation');
new Choices(selectFormation, {
    searchEnabled: true,
    searchPlaceholderValue: 'Rechercher une formation',
    itemSelectText: '',
    noResultsText: 'Aucune formation trouvée',
    noChoicesText: 'Aucune formation disponible',
    shouldSort: false,
});


//La fonction prépare des graphique vide et vérifie si l'id des graphiques existent bien dans le template graphique.html 
function CamembertVide(id) {
    const ctx = document.getElementById(id);
    if (!ctx) return null;
    return new Chart(ctx, {
        type: 'pie',
        data: { labels: [], datasets: [{ data: [] }] },
        options: {
            responsive: true,
            legend: { position: 'bottom' }
        }
    });
}

//on stocke les graphiques vides dans des variables. Ils seront mis à jour avec update() lorsque les données sont reçues avec fetch()
const graphBoursiers = CamembertVide('graphique_boursiers');
const graphSexe      = CamembertVide('graphique_sexe');
const graphFiliere   = CamembertVide('graphique_filiere');
const graphMention   = CamembertVide('graphique_mention');

// on récupère les paramètres de l'url qui correspondent aux choix de l'utiliateur
const params      = new URLSearchParams(window.location.search); //récupère une partie de l'url qui correspond aux choix utilisateur, transforme ce choix en objet qu'on peux récupérer avec get
const formationId = params.get('formation_id');
const annee       = params.get('annee');
const situation   = params.get('situation') || 'admis';

// définition d'une fonction pour remplir les graphiques existants avec des données, on modifie les labels et valeurs vides
function remplirCamembert(graphe, labels, valeurs) {
    graphe.data.labels = labels;
    graphe.data.datasets[0].data = valeurs;
    graphe.options.plugins = { colorschemes: { scheme: 'tableau.Tableau10' } };
    graphe.update(); //met à jour le graphique vide définit plus haut avec les données reçues
}

// si formation et année sont sélectionnées, fetch() est lancé
// fetch() envoie une requête vers la route avec les paramètres de l'utilisateur en url 
if (formationId && annee) {
    const urlApi = urlDonnees
        .replace(0, formationId)
        .replace(0, annee)
        .replace('SITUATION_DATA', situation);

    //conversion de la réponse en json
    fetch(urlApi)
        .then(response => response.json())
        //on remplit les graphiques avec le json
        .then(data => {
            if (!data || Object.keys(data).length === 0) {
                document.getElementById('resume').innerHTML = "Aucune donnée disponible pour cette sélection.";
                return;
            }

            // affichage de la capacité
            const capaciteE = document.getElementById('info-capacite');
            if (capaciteE) capaciteE.textContent = data.capacite ? `Capacité moyenne : ${data.capacite} places` : '';

            //ensuite, on remplit chaque graphique individuellement avec les données reçues par fetch()
            // Remplissage de chaque graphique si les données existent
            if (graphBoursiers && data.pct_boursiers !== null)
                remplirCamembert(graphBoursiers,
                    ['Boursiers', 'Non boursiers'],
                    [data.pct_boursiers, 100 - data.pct_boursiers]);

            if (graphSexe && data.pct_femmes !== null)
                remplirCamembert(graphSexe,
                    ['Femmes', 'Hommes'],
                    [data.pct_femmes, 100 - data.pct_femmes]);

            if (graphFiliere && data.pct_generale !== null)
                remplirCamembert(graphFiliere,
                    ['Générale', 'Technologique', 'Professionnelle'],
                    [data.pct_generale, data.pct_techno, data.pct_pro]);

            if (graphMention && data.pct_sm !== null)
                remplirCamembert(graphMention,
                    ['Très bien', 'Bien', 'Assez bien', 'Sans mention'],
                    [data.pct_tb, data.pct_bien, data.pct_ab, data.pct_sm]);

            // on remplit le résumé en bas de la page dynamiquement à partir des données reçues via fetch()
            document.getElementById('resume').innerHTML = `
                <div class="row text-center text-md-start">
                    <div class="col-md-4 border-end">
                    <h6 class="text-primary border-bottom pb-2">Profils</h6>
                        <ul class="list-unstyled mt-3">
                            <li><strong>Part de boursiers :</strong> ${data.pct_boursiers ?? 'N/A'} %</li>
                            <li><strong>Part de femmes :</strong> ${data.pct_femmes ?? 'Non disponible'} %</li>
                        </ul>
                    </div>
                    <div class="col-md-4 border-end">
                    <h6 class="text-primary border-bottom pb-2">Filière d'origine</h6>
                        <ul class="list-unstyled mt-3">
                            <li><strong>Filière générale :</strong> ${data.pct_generale ?? 'N/A'} %</li>
                            <li><strong>Filière technologique :</strong> ${data.pct_techno ?? 'N/A'} %</li>
                            <li><strong>Filière professionnelle :</strong> ${data.pct_pro ?? 'N/A'} %</li>
                        </ul>
                    </div>
                    <div class="col-md-4 border-end">
                    <h6 class="text-primary border-bottom pb-2">Mentions au bac</h6>
                        <ul class="list-unstyled mt-3">
                                <li><strong>Très bien :</strong> ${data.pct_tb} %</li>
                                <li><strong>Bien :</strong> ${data.pct_bien} %</li>
                                <li><strong>Assez bien :</strong> ${data.pct_ab} %</li>
                                <li><strong>Sans mention :</strong> ${data.pct_sm} %</li>
                            </ul>
                    </div>
                </div>`;
        });
}
