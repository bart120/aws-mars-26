# TP Lambda 101 — Traitement d’images serverless  
## Amazon S3 → AWS Lambda → Amazon S3  
### + CloudWatch Logs & Metrics

---

## 🎯 Objectif général

Découvrir le **serverless** avec AWS Lambda à travers un cas concret :  
le **traitement automatique d’images** lors d’un dépôt dans Amazon S3.

Ce TP constitue la base de tous les TPs Lambda suivants.

---

## 🧠 Objectifs pédagogiques

À l’issue de ce TP, vous serez capable de :

- Expliquer le principe du **serverless**
- Déclencher une fonction Lambda via un **événement S3**
- Traiter un fichier avec une **librairie externe (Pillow)**
- Gérer les permissions via **IAM**
- Utiliser des **variables d’environnement**
- Analyser les **logs CloudWatch**
- Publier une **métrique CloudWatch personnalisée**

---

## 🧱 Architecture cible

S3 (bucket source)  
→ Lambda (traitement image)  
→ S3 (bucket destination)  
→ CloudWatch (logs + métriques)

---

## 📌 Contraintes techniques

- Région : **eu-west-3 (Paris)**
- Runtime Lambda : **Python 3.12**
- Déclenchement : S3 `ObjectCreated`
- Filtrage sur types d’images
- Aucune instance EC2
- Aucune clé AWS dans le code

---

## 📦 Livrables attendus

- 2 buckets S3 (source / destination)
- 1 fonction Lambda opérationnelle
- Miniatures générées automatiquement
- Logs visibles dans CloudWatch
- Métrique personnalisée `ImagesProcessed`

---

## 🪜 Étape 1 — Buckets S3

Créer deux buckets dans la même région :

- `tp-lambda-images-source-<prenom>`
- `tp-lambda-images-thumb-<prenom>`

Les images seront déposées dans le bucket source.

---

## 🪜 Étape 2 — Rôle IAM Lambda

Créer un rôle IAM pour Lambda avec les permissions suivantes :

- Lire les objets S3 source
- Écrire les objets S3 destination
- Écrire des logs CloudWatch
- Publier des métriques CloudWatch

---

## 🪜 Étape 3 — Lambda Layer (Pillow)

La fonction Lambda utilise la librairie **Pillow** pour le traitement d’images.

Le layer doit être :
- compatible **Amazon Linux**
- compatible **Python 3.12**
- architecture **x86_64**

Le layer sera attaché à la Lambda.

---

## 🪜 Étape 4 — Fonction Lambda

Créer une fonction Lambda :

- Nom : `tp-lambda-thumbnail`
- Runtime : Python 3.12
- Mémoire : 512 MB
- Timeout : 60 secondes

### Variables d’environnement
- `DEST_BUCKET`
- `THUMB_SIZE`
- `OUTPUT_FORMAT`
- `KEY_PREFIX`
- `ALLOWED_EXTENSIONS`
- `METRIC_NAMESPACE`

---

## 🪜 Étape 5 — Déclencheur S3

Configurer une notification S3 :

- Événement : `ObjectCreated`
- Filtres :
  - suffix `.jpg`
  - suffix `.png`
- Destination : Lambda `tp-lambda-thumbnail`

---

## 📊 Étape 6 — CloudWatch

### Logs
- Groupe : `/aws/lambda/tp-lambda-thumbnail`
- Logs JSON structurés

### Métrique personnalisée
- Namespace : `INOW/Lambda101`
- Metric name : `ImagesProcessed`

---

## 🧪 Tests attendus

1. Upload image valide → miniature créée
2. Upload fichier non image → ignoré + log
3. Vérifier les logs CloudWatch
4. Vérifier la métrique `ImagesProcessed`

---

## 🧹 Nettoyage

- Supprimer la Lambda
- Supprimer les buckets S3
- Supprimer le layer
- Supprimer les logs CloudWatch si nécessaire