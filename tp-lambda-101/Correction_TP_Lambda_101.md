# CORRIGÉ FORMATEUR — TP Lambda 101  
## Traitement d’images serverless avec Amazon S3 & AWS Lambda

---

## 🧱 Architecture finale validée

S3 (bucket source)  
→ Lambda `tp-lambda-thumbnail`  
→ S3 (bucket destination)  
→ CloudWatch (Logs + Metrics)

---

## 🪜 Étape 1 — Création des buckets S3

### Buckets à créer
- `tp-lambda-images-source-<prenom>`
- `tp-lambda-images-thumb-<prenom>`

### Paramètres
- Région : eu-west-3
- Block Public Access : **ON**
- Versioning : désactivé (non requis)
- Aucun accès public

👉 **Point pédagogique** :  
S3 est utilisé ici comme **déclencheur événementiel**, pas comme simple stockage.

---

## 🪜 Étape 2 — Rôle IAM pour Lambda

### Rôle
- Type : Lambda
- Nom conseillé : `tp-lambda-thumbnail-role`

### Policy minimale (inline)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadSourceBucket",
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::tp-lambda-images-source-*/*"
    },
    {
      "Sid": "WriteDestBucket",
      "Effect": "Allow",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::tp-lambda-images-thumb-*/*"
    },
    {
      "Sid": "Logs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    },
    {
      "Sid": "Metrics",
      "Effect": "Allow",
      "Action": "cloudwatch:PutMetricData",
      "Resource": "*"
    }
  ]
}
```

👉 **Point pédagogique** :  
- `AWSLambdaBasicExecutionRole` ne suffit pas pour S3 et les métriques.
- Principe du **least privilege**.

---

## 🪜 Étape 3 — Lambda Layer Pillow

### Pourquoi un layer ?
- Pillow contient du code natif (`_imaging`)
- Il doit être compilé pour **Amazon Linux**
- Séparation code / dépendances

### Méthode recommandée
Création via **CloudShell** ou **Docker Amazon Linux**.

### Structure attendue du zip
```
pillow-layer.zip
└── python/
    └── PIL/
        ├── __init__.py
        ├── _imaging.cpython-312-x86_64-linux-gnu.so
        └── ...
```

### Paramètres du layer
- Nom : `pillow-py312`
- Runtime compatible : Python 3.12
- Architecture : x86_64

👉 **Erreur classique** :  
Layer compilé sur macOS / Windows → erreur `_imaging`.

---

## 🪜 Étape 4 — Fonction Lambda

### Paramètres
- Nom : `tp-lambda-thumbnail`
- Runtime : Python 3.12
- Architecture : x86_64
- Mémoire : **512 MB**
- Timeout : **60 s**
- VPC : **Aucun**

👉 **Point pédagogique** :  
Lambda hors VPC = plus simple, plus rapide, moins cher.

---

### Variables d’environnement

| Nom | Exemple |
|---|---|
| DEST_BUCKET | tp-lambda-images-thumb-vl |
| THUMB_SIZE | 200 |
| OUTPUT_FORMAT | JPEG |
| KEY_PREFIX | thumb_ |
| ALLOWED_EXTENSIONS | .jpg,.jpeg,.png |
| METRIC_NAMESPACE | INOW/Lambda101 |

---

## 🪜 Étape 5 — Code Lambda (référence)

Le code final doit inclure :
- Filtrage par extension
- Logs JSON structurés
- Gestion d’erreurs explicite
- Publication de métrique CloudWatch

👉 Référence : code validé fourni séparément (support Git / correction).

---

## 🪜 Étape 6 — Déclencheur S3

### Configuration
- Bucket : source
- Événement : `ObjectCreated`
- Filtres :
  - suffix `.jpg`
  - suffix `.png`
- Destination : Lambda `tp-lambda-thumbnail`

👉 **Point pédagogique** :  
Le filtrage côté S3 est **plus efficace** que dans le code.

---

## 🪜 Étape 7 — Tests & validation

### Test nominal
1. Upload image `.jpg`
2. Miniature créée dans bucket destination
3. Logs visibles
4. Métrique `ImagesProcessed` incrémentée

### Test négatif
- Upload `.txt`
- Aucun traitement
- Log “ignored”

---

## 📊 Étape 8 — CloudWatch

### Logs
- Groupe : `/aws/lambda/tp-lambda-thumbnail`
- Logs applicatifs JSON
- Logs système (REPORT)

### Métriques
- Namespace : `INOW/Lambda101`
- Metric : `ImagesProcessed`

👉 **Point pédagogique clé** :  
Logs ≠ métriques  
- Logs = diagnostic
- Métriques = pilotage

---

## 🧹 Nettoyage

- Supprimer la Lambda
- Supprimer le layer
- Supprimer les buckets S3
- Supprimer les log groups si nécessaire

