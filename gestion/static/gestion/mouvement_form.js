/* Avertissement de stock négatif à la saisie (issue #59) :
 * amélioration progressive, aucune ressource externe.
 *
 * Pour un formulaire de sortie de stock, affiche ou masque dynamiquement
 * un avertissement si la quantité saisie rendrait le stock négatif.
 * L'enregistrement reste possible dans tous les cas (informer, jamais bloquer).
 */
(function () {
    "use strict";

    document.addEventListener("DOMContentLoaded", function () {
        // Vérifier si nous sommes sur une page de sortie de stock
        var titre = document.querySelector("h1");
        if (!titre || !titre.textContent.includes("Sortie de stock")) {
            return;
        }

        // Récupérer le stock actuel depuis le data attribute sur le champ quantité
        var champQuantite = document.getElementById("id_quantite");
        if (!champQuantite) {
            return;
        }

        var stockActuel = parseFloat(champQuantite.dataset.stockActuel) || 0;
        var champAvertissement = document.getElementById("avertissement-stock-negatif");
        
        // Créer l'avertissement s'il n'existe pas (fallback)
        if (!champAvertissement) {
            champAvertissement = document.createElement("p");
            champAvertissement.id = "avertissement-stock-negatif";
            champAvertissement.className = "avertissement-stock-negatif";
            champAvertissement.textContent = "⚠️ Ce mouvement rendrait le stock négatif. L'enregistrement reste possible, mais une correction d'inventaire sera nécessaire.";
            champAvertissement.style.display = "none";
            
            // Insérer avant le formulaire
            var formulaire = document.querySelector("form");
            if (formulaire) {
                formulaire.parentNode.insertBefore(champAvertissement, formulaire);
            }
        }

        function mettreAJourAvertissement() {
            var quantite = parseFloat(champQuantite.value) || 0;
            
            // Afficher l'avertissement si quantité > 0 et stock - quantité < 0
            var afficherAvertissement = quantite > 0 && (stockActuel - quantite) < 0;
            
            champAvertissement.style.display = afficherAvertissement ? "" : "none";
        }

        // Écouter les changements sur le champ quantité
        champQuantite.addEventListener("input", mettreAJourAvertissement);
        champQuantite.addEventListener("change", mettreAJourAvertissement);
        
        // Initialiser l'affichage (masqué à l'ouverture)
        mettreAJourAvertissement();
    });
})();
