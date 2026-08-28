'use strict';

/* Admin Reine — date_naissance : si l'utilisateur ne tape que l'année
 * (4 chiffres), on la complète en 01/04/AAAA à la sortie du champ
 * (convention personnelle : 1er avril = reprise de l'année apicole).
 * Toute autre saisie (date complète, sélecteur calendrier) est laissée
 * intacte. */
(function () {
    function completerAnneeSeule(event) {
        var champ = event.target;
        var valeur = champ.value.trim();

        if (/^\d{4}$/.test(valeur)) {
            champ.value = '01/04/' + valeur;
        }
    }

    document.addEventListener('DOMContentLoaded', function () {
        var champDateNaissance = document.getElementById('id_date_naissance');
        if (champDateNaissance) {
            champDateNaissance.addEventListener('blur', completerAnneeSeule);
        }
    });
})();
