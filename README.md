# TP_Agile

tp méthode agile
trello 
https://trello.com/invite/b/6adb04ce2f11e2e78bc3badc/ATTIf6ad3101412ddb56d6bba2c3de2922a243425326/tpagile

Pydantic ou Langchain

# PROMPT DE RÉFÉRENCE — PROJET SCRUM AUTOMATISÉ PAR IA

## 1. Contexte général du projet

Nous développons une application web de gestion de projet agile reposant sur une architecture multi-agents IA.

L'objectif est d'automatiser la transformation d'une idée ou d'un besoin métier en un projet structuré, comprenant des User Stories, un backlog de tâches priorisé et des propositions de sprints.

L'application doit simplifier le travail de préparation d'un projet pour les clients, Product Owners, Scrum Masters et équipes de développement.

Le système doit être capable de comprendre un projet décrit en langage naturel, de poser les bonnes questions pour clarifier les besoins, puis de produire une organisation cohérente et exploitable par une équipe de développement.

Le processus repose sur plusieurs agents IA spécialisés, chacun ayant un rôle précis et transmettant ses résultats au suivant.

L'application doit fonctionner avec un niveau d'autonomie élevé, tout en laissant à l'utilisateur la possibilité de comprendre, modifier et contrôler les résultats générés.

## 2. Objectifs fonctionnels

L'application doit permettre à un utilisateur de :

1. Décrire son projet en langage naturel, par écrit ou au cours d'une conversation avec une IA.
2. Répondre à des questions dynamiques permettant de préciser les besoins et les contraintes du projet.
3. Obtenir une synthèse structurée des besoins.
4. Générer automatiquement des User Stories pertinentes.
5. Transformer ces User Stories en un backlog organisé comprenant les tâches fonctionnelles et techniques nécessaires.
6. Identifier les dépendances entre les tâches.
7. Estimer leur charge de travail et les prioriser.
8. Générer des propositions de sprints en fonction de la capacité de l'équipe.
9. Visualiser et modifier le backlog depuis une interface web interactive.
10. Réorganiser manuellement les tâches et conserver ses modifications.
11. Régénérer ou actualiser le backlog lorsque les besoins, les contraintes ou le périmètre du projet évoluent.

Le système doit produire des résultats compréhensibles, cohérents et suffisamment détaillés pour servir de base au travail d'une véritable équipe de développement.

## 3. Parcours utilisateur cible

Le parcours nominal est le suivant :

**Étape 1 — Description du projet**

L'utilisateur décrit librement son idée, son produit ou son projet. Il peut échanger avec le Product Owner IA sous forme de conversation.

**Étape 2 — Clarification des besoins**

Le Product Owner analyse la description et pose des questions adaptées, une par une. Les réponses peuvent être données sous forme de QCM ou de texte libre.

**Étape 3 — Synthèse**

Les informations collectées sont consolidées dans un contexte projet structuré, incluant les objectifs, les fonctionnalités principales, les utilisateurs cibles et les contraintes.

**Étape 4 — Génération des User Stories**

Un agent spécialisé transforme les besoins en User Stories cohérentes et détecte les doublons ou les incohérences.

**Étape 5 — Construction du backlog**

Un autre agent transforme les User Stories en éléments de backlog, en incluant les tâches fonctionnelles et techniques pertinentes.

**Étape 6 — Priorisation et estimation**

L'agent Scrum analyse les tâches, identifie leurs dépendances, estime leur charge de travail et détermine leur ordre de priorité.

**Étape 7 — Proposition de sprint**

Le système propose une organisation du travail en fonction de la capacité disponible de l'équipe et des échéances.

**Étape 8 — Restitution dans l'interface**

Le backlog, les priorités et les sprints proposés sont affichés dans une interface web interactive.

**Étape 9 — Ajustements**

L'utilisateur peut réorganiser les tâches, modifier certains éléments, changer les contraintes ou demander une nouvelle génération du backlog.

## 4. Architecture fonctionnelle multi-agents

L'application doit s'appuyer sur des agents spécialisés, coordonnés par un orchestrateur central.

### Agent 1 — Product Owner IA

**Responsabilité : comprendre le besoin métier.**

Cet agent constitue le point d'entrée principal du système.

Il doit :
- Comprendre la description initiale du projet.
- Dialoguer avec l'utilisateur.
- Identifier les informations manquantes.
- Générer des questions adaptées sous forme de QCM ou de champs de texte.
- Poser une question à la fois et adapter les suivantes aux réponses reçues.
- Collecter les contraintes fonctionnelles, techniques et organisationnelles.
- Clarifier les ambiguïtés importantes.
- Produire une synthèse structurée du projet avant de transmettre le contexte au prochain agent.

Les informations minimales à collecter sont :
- Les fonctionnalités principales.
- Les utilisateurs cibles.
- Les contraintes techniques.
- Le nombre de développeurs disponibles.
- Le budget.
- La date limite de livraison.

L'agent doit distinguer les informations confirmées, les hypothèses et les informations inconnues. Il ne doit pas inventer des contraintes ni présenter une estimation comme une donnée confirmée.

### Agent 2 — Générateur de User Stories

**Responsabilité : transformer les besoins en exigences fonctionnelles exploitables.**

Cet agent reçoit la synthèse du Product Owner et génère des User Stories selon le format :

« En tant que [type d'utilisateur], je souhaite [fonctionnalité] afin de [bénéfice attendu]. »

Il doit :
- Générer des User Stories pertinentes par rapport au périmètre du projet.
- Conserver le lien entre chaque User Story et le besoin initial.
- Vérifier les doublons.
- Détecter les incohérences avec les besoins initiaux.
- Fournir des critères d'acceptation lorsque cela est nécessaire pour clarifier le comportement attendu.
- Éviter les User Stories trop vagues, trop larges ou redondantes.

L'objectif est d'obtenir des User Stories suffisamment précises pour être transformées en tâches, sans imposer une décomposition technique excessive.

### Agent 3 — Générateur de backlog

**Responsabilité : transformer les User Stories en tâches structurées.**

Cet agent transforme les User Stories en éléments de backlog fonctionnels et techniques.

Il doit :
- Décomposer les User Stories en tâches pertinentes.
- Éviter de créer des tâches excessivement granulaires.
- Regrouper les opérations techniques qui constituent un même mécanisme fonctionnel lorsque cela est cohérent.
- Conserver le lien entre chaque tâche, sa User Story et son éventuelle Epic.
- Identifier les dépendances fonctionnelles et techniques.
- Fournir des données structurées exploitables directement par l'agent Scrum et l'interface web.

Exemple : pour une fonctionnalité de connexion, le backlog peut comprendre une tâche de mise en place du mécanisme d'authentification, sans créer artificiellement une tâche distincte pour chaque champ du formulaire.

### Agent 4 — Agent Scrum

**Responsabilité : estimer, prioriser et organiser le travail.**

Cet agent reçoit le backlog et produit une proposition d'organisation cohérente.

Il doit :
- Analyser la valeur métier des tâches.
- Évaluer leur importance fonctionnelle.
- Identifier les dépendances.
- Tenir compte de la date limite de livraison.
- Estimer la complexité et la charge de travail.
- Déterminer un ordre de priorité.
- Proposer une répartition en sprints en fonction de la capacité de l'équipe.
- Expliquer les raisons de ses décisions.

Les critères principaux de priorisation sont :
1. Valeur métier.
2. Importance fonctionnelle.
3. Dépendances.
4. Date limite de livraison.

L'estimation de la charge de travail est réalisée à cette étape. Le nombre de développeurs disponibles est une donnée obligatoire à prendre en compte pour les propositions de sprints.

Le résultat doit présenter, pour chaque tâche, une priorité, une estimation et une justification compréhensible.

Les tâches ayant des dépendances bloquantes doivent être ordonnées de façon cohérente. Une tâche ne doit pas être considérée comme réalisable avant ses prérequis indispensables.

### Orchestrateur central

L'orchestrateur pilote l'ensemble du processus.

Il doit :
- Déclencher les agents dans le bon ordre.
- Transmettre le contexte et les résultats nécessaires à chaque étape.
- Vérifier la validité des sorties.
- Gérer les erreurs et les nouvelles tentatives.
- Contrôler la cohérence entre les différentes étapes.
- Déclencher une nouvelle analyse lorsqu'une modification rend des résultats précédents obsolètes.
- Maintenir l'état du projet et le suivi de son traitement.

L'orchestrateur est responsable de la coordination. Les agents restent spécialisés et ne doivent pas dupliquer inutilement les responsabilités des autres.

## 5. Règles de priorisation et de planification

Le backlog doit être présenté dans un ordre allant de la priorité la plus élevée à la plus faible.

L'agent Scrum doit associer à chaque tâche :
- Un niveau de priorité.
- Une justification.
- Une estimation de charge.
- Les dépendances éventuelles.
- Un lien vers la User Story correspondante.
- Les informations utiles à sa planification.

Les dépendances ne doivent pas être traitées comme un simple critère secondaire : elles constituent également des contraintes d'ordre. Une tâche bloquée par un prérequis doit être signalée et ne doit pas être planifiée avant ce prérequis.

Le système doit pouvoir proposer des sprints, mais il ne doit pas prétendre calculer une capacité précise à partir du seul nombre de développeurs. En l'absence de données suffisantes, il doit utiliser des hypothèses explicites et demander des informations complémentaires lorsque cela est nécessaire.

La planification devra pouvoir évoluer lorsque les tâches, les estimations, les contraintes ou la disponibilité de l'équipe changent.

## 6. Interface web

L'interface web est un composant central du projet.

Elle doit présenter les résultats du travail des agents sous une forme claire, interactive et compréhensible.

### Vue backlog

La vue backlog doit permettre :
- D'afficher les tâches dans l'ordre de priorité.
- De consulter les User Stories associées.
- De visualiser les estimations et les dépendances.
- De comprendre les raisons de la priorisation.
- De réorganiser les tâches manuellement.
- De modifier les informations pertinentes.
- De conserver les modifications apportées.

### Vue Kanban

Une vue Kanban doit permettre de visualiser les tâches selon leur état d'avancement, par exemple :
- À faire.
- En cours.
- Terminé.

Le déplacement d'une tâche d'une colonne à une autre doit modifier son statut et être enregistré.

La priorité et le statut sont deux notions distinctes : déplacer une tâche dans le Kanban ne doit pas nécessairement modifier sa priorité.

### Vue des sprints

L'utilisateur doit pouvoir consulter les sprints proposés et les tâches qui leur sont affectées.

Le système doit permettre de comprendre :
- Les tâches sélectionnées pour chaque sprint.
- La charge estimée.
- La capacité disponible de l'équipe.
- Les dépendances et les éventuels blocages.
- Les raisons pour lesquelles certaines tâches sont planifiées avant d'autres.

### Interactions avec l'IA

L'interface doit également permettre de demander une actualisation du backlog lorsque les besoins évoluent.

Le système doit, autant que possible, réutiliser les éléments déjà validés et recalculer uniquement les parties impactées. Il doit signaler les changements importants plutôt que remplacer silencieusement le travail de l'utilisateur.

Les modifications manuelles de priorité doivent être conservées comme préférences explicites de l'utilisateur, sauf demande de réoptimisation. Le système doit néanmoins avertir l'utilisateur si une modification crée une incohérence avec une dépendance bloquante.

## 7. Architecture technique et échanges entre agents

Les technologies définitives restent à choisir collectivement en fonction des compétences de l'équipe, des contraintes du projet et de la facilité de maintenance.

L'architecture devra privilégier :
- Une séparation claire entre frontend et backend.
- Des agents modulaires et spécialisés.
- Un orchestrateur central.
- Des échanges de données structurés, de préférence au format JSON avec validation de schéma.
- Une gestion centralisée de l'état du projet.
- Une persistance des projets, des résultats générés et des modifications manuelles.
- Une gestion robuste des erreurs.
- Une traçabilité des décisions importantes.
- Une séparation entre les propositions de l'IA et les règles de cohérence du système.

Les contrats de données entre les agents devront être définis avant d'implémenter les échanges.

Les objets principaux pourront comprendre :
- ProjectContext.
- UserStory.
- BacklogTask.
- Dependency.
- PriorityAssessment.
- Sprint.
- TeamCapacity.
- ProjectRevision.

Chaque objet devra disposer d'un identifiant stable et des références nécessaires aux autres objets.

Les modifications du projet devront être versionnées ou, au minimum, permettre de distinguer les éléments générés par l'IA des modifications apportées par l'utilisateur.

Aucun agent ne doit être obligé de transmettre du texte libre lorsqu'une structure de données définie est nécessaire à l'étape suivante.

## 8. Gestion des évolutions et de la régénération

Le système doit être conçu pour gérer les changements de besoins.

Lorsqu'un utilisateur modifie une contrainte, une fonctionnalité ou une échéance, l'application doit :
1. Identifier les éléments du projet concernés.
2. Déterminer quelles User Stories et tâches doivent être réévaluées.
3. Relancer les agents nécessaires.
4. Actualiser les dépendances, estimations, priorités ou sprints impactés.
5. Préserver autant que possible les modifications manuelles.
6. Présenter les changements significatifs à l'utilisateur.

L'objectif n'est pas de reconstruire systématiquement l'intégralité du projet, mais de maintenir la cohérence du backlog tout au long de son évolution.

## 9. Principes de conception

Tous les développements doivent respecter les principes suivants :

**Cohérence métier :** les résultats doivent rester alignés sur les besoins exprimés par le client.

**Modularité :** chaque agent doit pouvoir être développé, testé et amélioré indépendamment.

**Traçabilité :** chaque User Story et chaque tâche doivent pouvoir être reliées à leur origine.

**Explicabilité :** les priorités, estimations et propositions de sprints doivent être justifiables.

**Robustesse :** les sorties des agents doivent être validées et les erreurs doivent être gérées explicitement.

**Contrôle utilisateur :** les modifications manuelles doivent être conservées et ne pas être écrasées silencieusement.

**Pragmatisme :** la décomposition des tâches doit rester utile à l'équipe de développement, sans générer une multitude de micro-tâches artificielles.

**Évolutivité :** l'architecture doit permettre d'ajouter de nouveaux agents et de nouvelles fonctionnalités sans remettre en cause l'ensemble du système.

**Séparation des responsabilités :** l'IA propose, analyse et génère ; le système vérifie les contraintes structurelles et applique les règles de cohérence.

## 10. Organisation du développement en équipe

Tous les membres de l'équipe doivent s'appuyer sur ce document comme contexte commun.

Avant de développer une fonctionnalité, chaque membre doit :
1. Comprendre son rôle dans le parcours global.
2. Identifier les agents, composants et données concernés.
3. Respecter les contrats de données définis.
4. Vérifier les dépendances avec les autres parties du système.
5. Éviter de réimplémenter une responsabilité déjà attribuée à un autre composant.
6. Documenter les décisions techniques ayant un impact sur l'architecture commune.

Les responsabilités pourront être réparties entre :
- Frontend et expérience utilisateur.
- Backend et persistance.
- Agents IA et conception des prompts.
- Orchestration multi-agents.
- Modèles de données et validation.
- Tests, intégration et déploiement.

Cette répartition est indicative et devra être adaptée à la composition réelle de l'équipe.

Les décisions structurantes doivent être partagées avant leur implémentation lorsqu'elles affectent plusieurs composants.

## 11. Critères de réussite du projet

La première version sera considérée comme fonctionnellement réussie lorsqu'un utilisateur pourra :

1. Décrire un projet en langage naturel.
2. Répondre à un questionnaire adaptatif du Product Owner IA.
3. Obtenir des User Stories cohérentes avec ses besoins.
4. Obtenir un backlog structuré comprenant des tâches fonctionnelles et techniques pertinentes.
5. Visualiser les dépendances et les priorités des tâches.
6. Obtenir des estimations de charge et une proposition de sprint tenant compte du nombre de développeurs disponibles.
7. Visualiser les tâches dans un backlog et un Kanban interactifs.
8. Réorganiser les tâches et conserver ses modifications.
9. Modifier les besoins et obtenir une actualisation cohérente des éléments impactés.

Les résultats devront être suffisamment fiables et explicables pour servir de base de travail à une équipe de développement, sans prétendre remplacer systématiquement le jugement humain.

## 12. Consigne générale pour tout travail réalisé sur ce projet

Toute personne ou IA intervenant sur ce projet doit utiliser ce document comme contexte de référence.

Avant de proposer une solution, une architecture ou une modification, elle doit vérifier que celle-ci :
- Respecte les objectifs du projet.
- S'intègre à l'architecture multi-agents.
- Respecte la séparation des responsabilités.
- Préserve la cohérence des données.
- Tient compte des dépendances entre les composants.
- Apporte une valeur concrète à la version en cours.

Si une décision importante n'est pas définie, il faut la signaler et proposer une solution argumentée plutôt que d'introduire silencieusement un choix technique ou fonctionnel.

Les recommandations doivent distinguer les exigences déjà définies, les choix proposés et les points restant à valider.

L'objectif commun est de construire une application modulaire, cohérente et évolutive, capable d'automatiser la préparation et l'organisation d'un projet agile grâce à plusieurs agents IA collaboratifs, tout en conservant une interface de contrôle claire pour l'utilisateur.
