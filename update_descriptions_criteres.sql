-- Ajoute une phrase d'intention ("ce que ça mesure") en tête de chaque
-- description de critère, avant le protocole déjà présent. Le contenu
-- du protocole (issu du cours Maranzan/CRISAB) n'est pas modifié.

UPDATE selection_critereselection SET description =
'Mesure l''état sanitaire général de la colonie. Examen visuel du couvain lors de la visite de printemps, à la recherche de traces de maladie. Note décroissante de 4 (aucune trace) à 1 (présence de maladie constatée).'
WHERE code = 'SANTE';

UPDATE selection_critereselection SET description =
'Mesure la propreté du fond de ruche, révélatrice de l''hygiène générale de la colonie. Observation de l''état du plateau (débris de cire, larves mortes). Note de 4 (plateau propre) à 1 (nombreux déchets avec plusieurs larves).'
WHERE code = 'PROPRETE';

UPDATE selection_critereselection SET description =
'Mesure le tempérament et la douceur de la colonie. « Test du bâton » : passer un bâton deux fois (aller-retour) devant l''entrée de la ruche, le matin avant la sortie des abeilles. Note de 4 (peu de sorties, pas de vol) à 1 (sortie en masse avec attaque).'
WHERE code = 'AGRESSIVITE';

UPDATE selection_critereselection SET description =
'Mesure le calme de la colonie lors des manipulations.  Un colonie qui "coule" des cadres est un mauvais signe concernant l''aggressivité. Après un léger enfumage, soulever un cadre de couvain ouvert et tapoter 5 à 6 fois la barrette supérieure. Note de 4 (les abeilles ne se déplacent pas) à 1 (elles forment des grappes et tombent).'
WHERE code = 'TENUE_CADRE';

UPDATE selection_critereselection SET description =
'Mesure le comportement hygiénique de la colonie (capacité à détecter et évacuer le couvain mort ou malade, liée à la résistance aux maladies). Désoperculer un carré d''environ 3x3 cm de couvain mâle, tuer les larves, puis chronométrer le temps nécessaire aux ouvrières pour les évacuer entièrement. Note de 4 (nettoyage en 3h) à 1 (12h).'
WHERE code = 'NETTOYAGE';

UPDATE selection_critereselection SET description =
'Mesure la productivité mellifère relative de la colonie. Comparaison de la récolte de miel de la colonie à la moyenne du rucher. Note de 4 (25% de plus que la moyenne) à 1 (récolte égale à la moyenne).'
WHERE code = 'RECOLTE';

UPDATE selection_critereselection SET description =
'Mesure le potentiel de développement de la colonie et la fécondité de la reine. Mesure du couvain par la formule grand diamètre x petit diamètre x nombre de cadres de couvain, ramenée à un nombre de cellules estimé. Note de 4 (environ 24000 cellules) à 1 (environ 6000 cellules).'
WHERE code = 'COUVAIN';

UPDATE selection_critereselection SET description =
'Mesure la capacité de la colonie à constituer ses réserves de miel(dans le corps). Estimation de la provision de miel de la colonie. Note de 4 (environ 7 kg) à 1 (environ 1 kg).'
WHERE code = 'MIEL';

UPDATE selection_critereselection SET description =
'Mesure l''approvisionnement en protéines de la colonie, essentiel au nourrissage du couvain. Estimation de la provision de pollen, convertie en surface de rayon operculé (1 dm² correspond à environ 150 g). Note attribuée selon le même principe dégressif que les autres critères de la passe approfondie.'
WHERE code = 'POLLEN';
