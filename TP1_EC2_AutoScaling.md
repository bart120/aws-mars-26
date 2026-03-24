# TP 1 — Mise en place d’une infrastructure scalable avec Amazon EC2  
## Auto Scaling Group + Application Load Balancer

---

## 🎯 Objectif général

Mettre en œuvre une **architecture scalable et hautement disponible** sur AWS en utilisant :

- Amazon EC2
- Application Load Balancer (ALB)
- Auto Scaling Group (ASG)
- Amazon CloudWatch

Ce TP permet de comprendre **le scaling horizontal**, la **haute disponibilité** et les **mécanismes d’élasticité** d’AWS.

---

## 🧠 Objectifs pédagogiques

À l’issue de ce TP, vous serez capable de :

- Déployer une application web simple sur EC2
- Configurer un **Application Load Balancer**
- Mettre en place un **Auto Scaling Group**
- Comprendre les **Scaling Policies**
- Tester le scaling via un **outil de charge**
- Observer le comportement via **CloudWatch**

---

## 🧱 Architecture cible

```
Internet
   ↓
Application Load Balancer
   ↓
Auto Scaling Group
   ↓
EC2 instances (AZ multiples)
```

---

## 📌 Contraintes techniques

- Région : **eu-west-3 (Paris)**
- Instances EC2 : Amazon Linux 2
- Type : t2.micro ou t3.micro
- Aucune IP publique sur les instances
- Accès uniquement via ALB
- Sécurité minimale (Security Groups)

---

## 📦 Livrables attendus

- 1 Application Load Balancer fonctionnel
- 1 Auto Scaling Group
- 1 Launch Template
- Instances EC2 créées automatiquement
- Scaling observé en charge
- Logs et métriques CloudWatch consultés

---

## 🪜 Étape 1 — Création du réseau (si nécessaire)

Si aucun VPC n’est disponible :
- Utiliser le **VPC par défaut**
- Vérifier :
  - 2 sous-réseaux dans des AZ différentes
  - Accès Internet (IGW)

---

## 🪜 Étape 2 — Launch Template EC2

Créer un **Launch Template** :

### Paramètres
- AMI : Amazon Linux 2
- Instance type : t2.micro
- Key pair : optionnel
- Security Group :
  - Autoriser HTTP (80) depuis le SG de l’ALB
- User Data :

```bash
#!/bin/bash
yum update -y
yum install -y httpd
systemctl start httpd
systemctl enable httpd
echo "Hello from $(hostname)" > /var/www/html/index.html
```

---

## 🪜 Étape 3 — Application Load Balancer

Créer un **ALB** :

- Type : Application Load Balancer
- Scheme : Internet-facing
- Listener :
  - HTTP : 80
- Target Group :
  - Type : Instance
  - Health check : `/`

---

## 🪜 Étape 4 — Auto Scaling Group

Créer un **Auto Scaling Group** :

### Paramètres
- Launch Template : celui créé précédemment
- Subnets : au moins 2 AZ
- Target Group : celui de l’ALB

### Capacité
- Desired : 1
- Min : 1
- Max : 4

---

## 🪜 Étape 5 — Scaling Policy

Créer une **Scaling Policy** :

- Type : Target Tracking
- Metric :
  - Average CPU Utilization
- Target value : 50 %

👉 Le scaling se déclenche automatiquement selon la charge CPU.

---

## 🧪 Étape 6 — Tests de montée en charge

### Test simple
Récupérer le DNS de l’ALB :
```
http://<ALB_DNS>
```

### Test de charge (exemple)
Depuis CloudShell ou une autre instance :

```bash
ab -n 100000 -c 200 http://<ALB_DNS>/
```

### Résultat attendu
- Augmentation du nombre d’instances EC2
- Répartition de la charge
- Réponses différentes selon le hostname

---

## 📊 Étape 7 — Observations CloudWatch

À observer :
- CPUUtilization
- NumberOfInstances (ASG)
- Health checks ALB

👉 Comprendre les délais :
- Warm-up
- Cooldown
- Scale-out / Scale-in

---

## 🧹 Nettoyage

- Supprimer l’Auto Scaling Group
- Supprimer l’ALB
- Supprimer le Launch Template
- Vérifier qu’aucune instance EC2 ne reste active
