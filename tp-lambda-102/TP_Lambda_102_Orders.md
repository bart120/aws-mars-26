# TP Lambda 102 — Traitement de commandes e-commerce  
## S3 → Lambda → SQS → Lambda → DynamoDB  
### + CloudWatch Metrics + CI/CD AWS (CodeCommit & CodePipeline)

---

## 🎯 Objectif général

Mettre en place une **architecture serverless asynchrone, découplée et résiliente** pour traiter des commandes e-commerce, en utilisant exclusivement des services managés AWS.

Ce TP prolonge directement **Lambda 101** et introduit :
- le **découplage par file de messages (SQS)**
- la **gestion des erreurs via DLQ**
- la **persistance d’état via DynamoDB**
- l’**observabilité applicative**
- un **pipeline CI/CD AWS-native** avec CodeCommit

---

## 🧠 Objectifs pédagogiques

À l’issue de ce TP, vous serez capable de :

- Expliquer une architecture **event-driven asynchrone**
- Découpler des traitements avec **Amazon SQS**
- Mettre en œuvre des **retries et une Dead Letter Queue**
- Implémenter une logique **idempotente**
- Stocker des états applicatifs dans **DynamoDB**
- Publier et analyser des **métriques CloudWatch personnalisées**
- Déployer automatiquement une Lambda via **CodeCommit + CodePipeline**

---

## 🧱 Architecture cible

S3 (orders/)  
→ Lambda Validator  
→ SQS Main Queue  
→ Lambda Worker  
→ DynamoDB (Orders)  
→ CloudWatch Metrics  
→ DLQ (en cas d’échec)

---

## 📌 Contraintes techniques

- Région : **eu-west-3 (Paris)**
- Runtime Lambda : **Python 3.12**
- Aucun serveur EC2
- Aucune clé AWS dans le code
- Déploiement automatisé

---

## 📦 Livrables attendus

- Bucket S3 avec préfixe `orders/`
- SQS main queue + DLQ
- Table DynamoDB `tp-orders`
- Lambdas `tp-order-validator` et `tp-order-worker`
- Pipelines CI/CD dédiés
- Métriques CloudWatch :
  - OrdersProcessed
  - OrdersRejected
  - OrdersDuplicate

---

## 🧾 Modèle de commande

### Commande valide
```json
{
  "order_id": "ORD-2026-001",
  "customer_id": "CUST-1001",
  "created_at": "2026-01-07T10:00:00Z",
  "currency": "EUR",
  "amount": 149.99,
  "items": [
    { "sku": "SKU-1", "qty": 1, "unit_price": 99.99 },
    { "sku": "SKU-2", "qty": 1, "unit_price": 50.00 }
  ]
}
```

### Commande invalide
```json
{
  "order_id": "ORD-2026-002",
  "customer_id": "CUST-1002",
  "created_at": "2026-01-07T10:05:00Z",
  "currency": "EUR",
  "amount": -10,
  "items": []
}
```

---

## 🧪 Tests attendus

1. Commande valide → PROCESSED + OrdersProcessed
2. Commande invalide → REJECTED + DLQ + OrdersRejected
3. Doublon → DUPLICATE + OrdersDuplicate
