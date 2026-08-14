# NetBox Force — Guide (français)

[← Toutes les langues](../README.md) · [README du projet](../../README.md) · [Journal des modifications](../../CHANGELOG.md)

---

## 1. Ce que fait le plugin

NetBox enregistre *ce qui* a changé. NetBox Force décide *si le changement est
seulement autorisé*, et peut exiger une justification avant de le laisser passer.

Il se place entre chaque opération d'enregistrement ou de suppression et la base
de données. Avant qu'un changement soit écrit, il peut vérifier :

- qu'un commentaire de journal a été fourni et qu'il est assez long
- que ce commentaire ne se limite pas à des mots creux
- que le commentaire mentionne un numéro de ticket
- que le changement se produit dans une plage horaire approuvée
- que les valeurs des champs respectent un motif de nommage
- que les champs obligatoires sont réellement remplis

Deux modules l'accompagnent :

- **Gestion des correctifs** — état des correctifs, système d'exploitation,
  responsables et historique des mises à jour par machine virtuelle ou serveur
  physique, alimenté au besoin depuis CheckMK.
- **Graylog** — envoie les événements d'audit vers l'extérieur et ramène les
  informations de journalisation à côté de l'objet concerné.

Tout est facultatif. Après l'installation, seule la vérification de présence du
commentaire est active, avec un minimum de deux caractères. Le reste s'active
depuis l'interface web.

---

## 2. Prérequis

| Composant | Version | Remarques |
|---|---|---|
| NetBox | 4.0.0 ou plus récent | |
| Python | 3.10 ou plus récent | |
| PostgreSQL | — | Exigé par NetBox lui-même |
| `cryptography` | quelconque | Fourni avec NetBox. Sans lui, le secret CheckMK et le jeton Graylog sont stockés en clair, et le plugin le signale sur la page des paramètres |
| `requests` | quelconque | Fourni avec NetBox. Nécessaire pour CheckMK et Graylog |
| Processus RQ | — | Uniquement pour la synchronisation CheckMK planifiée et la relève Graylog. Sans lui, les deux fonctionnent encore à la demande, et la page le signale |

---

## 3. Installation

### 3.1 Installer le paquet

```bash
source /opt/netbox/venv/bin/activate
pip install git+https://github.com/Gasi-Code/netbox-force.git
```

### 3.2 Déclarer le plugin

Dans `configuration.py` :

```python
PLUGINS = ['netbox_force']
```

### 3.3 Exécuter les migrations

```bash
cd /opt/netbox/netbox
python manage.py migrate netbox_force
python manage.py collectstatic --no-input
```

### 3.4 Redémarrer NetBox

```bash
sudo systemctl restart netbox netbox-rq
```

### 3.5 Docker

```bash
docker exec -it <conteneur> pip install git+https://github.com/Gasi-Code/netbox-force.git
docker exec -it <conteneur> /opt/netbox/netbox/manage.py migrate netbox_force
docker restart <conteneur>
```

Sur l'image LinuxServer.io, **n'utilisez pas** de scripts `custom-cont-init.d`
pour l'installation. Ils s'exécutent *après* les scripts d'initialisation de
NetBox, ce qui peut faire échouer les migrations. Les Docker Mods s'exécutent
avant.

Une installation faite dans le système de fichiers du conteneur ne survit pas à
une mise à jour de l'image. Ajoutez le plugin au mécanisme d'installation
persistant de l'image, sinon il disparaîtra au prochain pull.

---

## 4. Mise à jour

```bash
source /opt/netbox/venv/bin/activate
pip install --force-reinstall --no-cache-dir git+https://github.com/Gasi-Code/netbox-force.git
```

`--force-reinstall --no-cache-dir` est nécessaire parce que pip met en cache par
numéro de version et sauterait sinon la reconstruction d'une même version.

**Vérifiez avant de redémarrer.** Cette étape importe le plugin sans toucher au
processus en cours. En cas d'erreur, ne redémarrez pas : le NetBox en service a
encore l'ancien code en mémoire et continue de fonctionner :

```bash
cd /opt/netbox/netbox
python manage.py check
```

Ensuite :

```bash
python manage.py migrate netbox_force
python manage.py collectstatic --no-input
sudo systemctl restart netbox netbox-rq
```

### Revenir en arrière

```bash
pip install --force-reinstall --no-cache-dir \
  git+https://github.com/Gasi-Code/netbox-force.git@<commit>
sudo systemctl restart netbox netbox-rq
```

Les migrations n'ont généralement pas besoin d'être annulées. Les colonnes
supplémentaires ne gênent pas l'ancien code : il les ignore, tout simplement.
Faites tout de même une sauvegarde de la base avant la mise à jour.

---

## 5. Fichier de configuration

`PLUGINS_CONFIG` ne fixe **que les valeurs initiales**. Après le premier
démarrage, chaque paramètre est géré dans l'interface web et stocké en base.

```python
PLUGINS_CONFIG = {
    'netbox_force': {
        'min_length': 2,
        'exempt_users': ['automation', 'monitoring', 'netbox'],
        'enforce_on_create': False,
        'enforce_on_delete': True,
        'extra_exempt_models': [],
        'checkmk_secret': '',
    },
}
```

| Paramètre | Défaut | Signification |
|---|---|---|
| `min_length` | `2` | Nombre minimal de caractères dans un commentaire |
| `exempt_users` | voir ci-dessus | Utilisateurs exemptés de toute vérification, casse indifférente |
| `enforce_on_create` | `False` | Exiger un commentaire aussi à la création |
| `enforce_on_delete` | `True` | Exiger un commentaire aussi à la suppression |
| `extra_exempt_models` | `[]` | Modèles supplémentaires exemptés, format `app.model` |
| `checkmk_secret` | `''` | Facultatif. Garde le secret CheckMK entièrement hors de la base ; il prend alors le pas sur le champ de l'interface |

---

## 6. Les pages

Les superutilisateurs trouvent **NetBox Force** dans la barre latérale. Toutes les
pages sont réservées aux superutilisateurs sauf mention contraire.

| Page | Objet |
|---|---|
| **Paramètres** | Toutes les règles d'application, exemptions, modules, webhook, CheckMK |
| **Règles de validation** | Motifs de nommage et champs obligatoires, par modèle et par champ |
| **Politiques par modèle** | Dérogations aux paramètres globaux, par modèle |
| **Infractions** | Journal filtrable de chaque changement bloqué, exportable en CSV |
| **Graylog** | Envoi et lecture, voir les sections 7 et 8 |
| **Tableau de bord** | Statistiques : fonctions actives, changements bloqués, utilisateurs les plus fréquents, tendance sur 30 jours |
| **Modèles d'import** | Modèles CSV téléchargeables pour l'import en masse de NetBox. Visibles par tous les utilisateurs connectés lorsqu'activés |
| **Guide** | Page de texte libre pour vos propres utilisateurs. Visible par tous les utilisateurs connectés lorsqu'activée |
| **Gestion des correctifs** | Voir la section 9 |

Deux paramètres méritent une mention à part :

- **Interrupteur global** — suspend toutes les vérifications, par exemple pendant
  une fenêtre de maintenance.
- **Mode d'essai (dry-run)** — consigne les infractions sans rien bloquer. C'est
  la bonne façon d'introduire une nouvelle règle : on voit ce qui *aurait* été
  bloqué avant d'arrêter réellement quelqu'un.

---

## 7. Graylog — envoi

Envoie les événements d'audit de NetBox vers Graylog en GELF.

### Pourquoi

Trois choses ne sont consignées nulle part ailleurs dans NetBox :

- **Les échecs de connexion.** NetBox ne les conserve pas du tout.
- **L'adresse IP du client et l'agent utilisateur** d'un changement. Le journal
  des modifications de NetBox ne porte ni l'un ni l'autre.
- **Les modifications des paramètres du plugin lui-même.** Elles ne sont pas
  couvertes par le journal de NetBox : désactiver l'application des règles ne
  laissait auparavant aucune trace.

### Mise en place

Sur la page **Graylog**, moitié supérieure : hôte, port, transport. Puis *Envoyer
un événement de test*.

Commencez par **UDP**. Si rien n'arrive, passez à **TCP** : par construction, UDP
ne peut pas signaler d'échec, TCP le peut. Cela distingue « mauvais port » de
« message rejeté ».

| Transport | Confirme la livraison | Chiffré |
|---|---|---|
| UDP | non | non |
| TCP | oui | non |
| TCP + TLS | oui | oui |
| HTTP | oui | non |
| HTTPS | oui | oui |

UDP est correct dans un réseau local et incorrect à travers internet.

### Ce qui est envoyé

Une ligne par type d'événement, chacune avec une case à cocher et une gravité
syslog : objet créé, modifié, supprimé ; connexion ; déconnexion ; échec de
connexion ; changement bloqué ; paramètres du plugin modifiés.

### Volume

Une requête modifiant plus d'objets que le seuil configuré est signalée par **un
seul événement de synthèse**. Importer 500 équipements est une opération : 500
lignes presque identiques la rendent plus difficile à voir, pas plus facile.

Résumer plutôt que limiter le débit est un choix délibéré. Une file qui se vide
plus lentement qu'elle ne se remplit rejette les événements *les plus récents*,
soit précisément la mauvaise moitié.

### Noms des champs

Chaque événement porte les mêmes champs, pour que les recherches restent simples :

```
_app          netbox_force
_category     object_change | auth | violation | settings
_event        object_created, login_failed, …
_username
_client_ip
_user_agent
_object_type  dcim.device
_object_id
_object_name
_action       create | update | delete
_changed_fields
_request_id
_netbox_url
_outside_business_hours
```

`_request_id` regroupe tout ce qu'une requête a modifié. Quarante équipements
modifiés en une fois forment une opération, pas quarante énigmes.

### Trois points à connaître

- **Une panne de Graylog ne peut ni ralentir ni faire échouer un enregistrement
  dans NetBox.** Les événements passent par une file bornée qu'un fil d'arrière-plan
  vide. Quand la file est pleine, les nouveaux événements sont abandonnés et
  comptés, et le compteur est affiché sur la page.
- **Le texte du message est toujours en anglais**, quelle que soit la langue de
  l'interface. Les requêtes d'alerte Graylog s'appuient dessus ; le traduire
  casserait silencieusement toutes les alertes dès qu'on changerait la langue.
- **L'IP du client est lue depuis `X-Forwarded-For`** lorsqu'il est présent. Cet
  en-tête vient du client et peut être falsifié si NetBox est joignable sans proxy
  inverse devant lui.

---

## 8. Graylog — lecture

Ramène les informations de Graylog dans NetBox pour juger un hôte sans ouvrir un
second onglet.

### Mise en place

Moitié inférieure de la page **Graylog** : adresse web et jeton API, puis *Tester
la connexion*. Le résultat indique la version de Graylog, la forme d'API de
recherche détectée, les sources les plus bruyantes et les flux disponibles.
*Relever maintenant* lance une relève immédiate.

**Émettez le jeton pour un utilisateur Graylog doté d'un rôle en lecture seule.**
C'est cela, et non le code de ce plugin, qui garantit que Graylog ne peut pas être
modifié depuis NetBox.

### Ce que « lecture seule » signifie ici, précisément

Chaque appel récupère des données ou demande à Graylog d'exécuter une recherche.
L'ancien point d'accès de recherche est un simple `GET`. La nouvelle API de
recherche Views ne l'est pas : elle exige un `POST` pour enregistrer une recherche
et un autre pour l'exécuter. Cela crée un objet de recherche éphémère dans Graylog
et renvoie des résultats ; les données stockées ne sont pas modifiées. Si seul
`GET` est acceptable dans votre environnement, fixez la forme de recherche à
`legacy` dans les paramètres.

### Associer les sources aux objets NetBox

Exact, dans cet ordre, la première correspondance l'emporte :

| | Règle |
|---|---|
| 1 | **Association manuelle** — une fois posée, elle prime toujours |
| 2 | **Adresse IP** — la source face à toutes les IP de l'objet |
| 3 | **Nom d'hôte**, casse indifférente |
| 4 | **Nom d'hôte après suppression d'un suffixe de domaine configuré** |

Tout le reste demeure non associé et est listé comme tel.

**Il n'y a délibérément aucune correspondance approximative.** `srv-web-01` et
`srv-web-02` diffèrent d'un caractère : toute mesure de ressemblance les déclare
identiques à 96 % alors que ce sont deux machines différentes. Dans un schéma de
nommage numéroté — c'est-à-dire dans tout NetBox digne de ce nom — le candidat le
plus ressemblant est systématiquement le mauvais. Les journaux seraient classés
sous le serveur voisin sans que personne ne s'en aperçoive. La ressemblance sert
uniquement à **trier** les suggestions à côté d'une source non associée ; elle
n'associe jamais rien.

Si un relais syslog central se trouve devant Graylog, tous les messages portent
l'adresse du relais et la règle 2 ne trouve rien d'utile. Le champ source doit
alors porter le nom d'hôte, ce à quoi servent les règles 3 et 4.

### Les pages

- **Sources** — tout ce que Graylog signale, avec compteurs, filtrable par
  associées, non associées, silencieuses, jamais vues et ignorées.
- **Silencieuses** — associées dans NetBox mais n'envoyant plus rien. Mortes, mal
  configurées, ou vestige. Aucun des deux systèmes ne le repère seul.
- **Jamais vues dans Graylog** — l'autre moitié du recoupement.
- **Grappe** — nœuds avec voyant vert/orange/rouge, santé de l'indexeur, retard du
  journal, chaque nœud relié à sa machine virtuelle NetBox.
- **Sur l'objet** — les équipements et machines virtuelles disposant d'une source
  associée reçoivent un panneau Graylog avec compteurs, messages récents à la
  demande et lien vers Graylog.

### Charge et sûreté

- Une relève est **une seule requête groupée pour tous les hôtes**, et non une
  requête par équipement. Un site de 800 équipements coûte trois requêtes.
- Le panneau de grappe et la liste des messages se chargent **après** le rendu de
  la page. Un Graylog lent ou mort donne un panneau vide, jamais une page NetBox
  figée.
- L'association vit dans la table propre au plugin. **Graylog n'écrit jamais dans
  un objet central de NetBox** : retirer le plugin supprime l'association et laisse
  NetBox intact.
- Le point d'accès aux messages ne répond que pour une source associée à un objet
  que l'appelant a le droit de consulter.

---

## 9. Gestion des correctifs et CheckMK

Suit l'état des correctifs, le système d'exploitation, les responsables et
l'historique des mises à jour par machine virtuelle ou serveur physique.

- **État** vert / orange / rouge, tenu à la main ou lu depuis CheckMK.
- **Seuil de retard** — les entrées non corrigées en N jours sont marquées en
  retard.
- **Escalade** — une entrée restée N jours en *orange* passe seule au *rouge*.
- **Contacts** — administrateur et responsable de processus issus des objets de
  contact NetBox.
- **Historique des mises à jour** — une entrée par passage de correctifs, avec
  numéro de ticket et note.
- **L'accès** est accordé par nom de groupe NetBox dans les paramètres du plugin,
  et non par les permissions Django.

### CheckMK

L'intégration est un **pull** : NetBox lit depuis CheckMK. Rien n'est écrit dans
CheckMK, un utilisateur d'automatisation en lecture seule suffit donc.

Configuré sur la page des paramètres : URL du site, utilisateur d'automatisation,
secret, filtre de services et intervalle de synchronisation. Le secret est stocké
chiffré et n'est plus jamais affiché.

Une synchronisation bloquée est la panne qui fait le plus mal, car la page
continue d'afficher un état de correctifs qui a silencieusement cessé d'être vrai.
Le tableau de bord indique donc explicitement quand la dernière synchronisation
réussie est plus ancienne que le double de l'intervalle configuré.

---

## 10. Dépannage

**Le plugin n'apparaît pas dans la barre latérale.**
`PLUGINS` est-il défini dans `configuration.py` ? Les migrations ont-elles été
exécutées ? NetBox a-t-il été redémarré ? Les libellés de la barre latérale ne se
mettent à jour qu'au redémarrage ; les onglets internes au plugin, immédiatement.

**Les changements ne sont pas bloqués.**
Vérifiez, dans cet ordre : l'interrupteur global, le mode d'essai, si votre
utilisateur figure parmi les utilisateurs ou groupes exemptés, et si une politique
par modèle désactive l'application pour ce modèle.

**Une page signale une colonne manquante.**
Les migrations n'ont pas été exécutées, ou seulement en partie.
`python manage.py migrate netbox_force`.

**« Aucun processus d'arrière-plan ne tourne. »**
`netbox-rq` n'est pas lancé. La synchronisation CheckMK et la relève Graylog ne
s'exécutent alors que sur appui du bouton.

**Rien n'arrive dans Graylog.**
Passez le transport d'UDP à TCP. UDP ne peut pas signaler d'échec ; TCP le peut,
et son message d'erreur indique si le port est mauvais ou si le message a été
rejeté.

**Le panneau Graylog d'un équipement reste vide.**
L'équipement n'a pas de source associée. Ouvrez *Sources → Non associées* et
associez-la, ou ajoutez votre suffixe de domaine dans les paramètres pour que le
FQDN puisse être raccourci.

**Après un changement de `SECRET_KEY`, le secret CheckMK ou le jeton Graylog ne fonctionne plus.**
Les deux sont chiffrés avec une clé dérivée de `SECRET_KEY`. Il faut les saisir à
nouveau.

---

## 11. Changer de langue

La langue est un paramètre **par installation**, pas par utilisateur. Elle se
change sur la page des paramètres.

Les onglets et pages internes au plugin basculent immédiatement. Les libellés de
la barre latérale sont construits une seule fois au démarrage et ne changent
qu'après un redémarrage de NetBox.

Les messages affichés aux utilisateurs lors d'un blocage suivent ce paramètre. Les
messages d'erreur de l'API et ceux envoyés à Graylog restent en anglais — voir la
note dans l'[index de la documentation](../README.md).

---

## 12. Licence

AGPL-3.0. Voir [LICENSE](../../LICENSE).
