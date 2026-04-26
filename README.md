### ParkGuard AI — Smart Parking Management System

## objectif du Projet (Project Objective)
Ce projet consiste à concevoir un système intelligent capable de détecter et reconnaître automatiquement les plaques d’immatriculation des véhicules à partir du flux vidéo d'une caméra. 

L'application de bureau (standalone) est conçue pour gérer l'accès à un parking. Elle vérifie si le véhicule détecté appartient à un client enregistré et s'il a payé ses frais mensuels. 
- Si le client est autorisé et à jour dans ses paiements, le système enregistre l'accès et envoie un signal `OPEN` pour ouvrir la barrière.
- Si le client n'est pas enregistré ou n'a pas payé, l'accès est refusé (`DENIED`).

Un serveur HTTP léger est intégré pour permettre à une carte électronique (comme un Raspberry Pi, Jetson Nano ou Arduino) d'interroger l'état de la barrière et d'actionner le mécanisme physique.

## Technologies Utilisées (Tech Stack)
Ce projet combine le traitement d'images, le deep learning et le développement d'interfaces graphiques modernes :

- **Python 3** : Le langage de programmation principal.
- **CustomTkinter** : Utilisé pour créer l'interface graphique utilisateur (GUI) de bureau, offrant un design moderne en mode sombre (Premium Dark Theme).
- **YOLO (Ultralytics)** : Un modèle d'intelligence artificielle (Deep Learning) pré-entraîné (`best.pt`) utilisé pour localiser (détecter) les plaques d'immatriculation dans l'image.
- **EasyOCR** : Une bibliothèque de reconnaissance optique de caractères (OCR) basée sur le deep learning, utilisée pour extraire le texte (numéro) de la plaque détectée.
- **OpenCV** : Utilisé pour la capture du flux vidéo de la webcam et le prétraitement des images avant l'OCR.
- **SQLite** : Base de données légère intégrée pour gérer les clients, les paiements mensuels et l'historique des accès.
- **Flask / BaseHTTPRequestHandler** : Un serveur HTTP local (`gate_server.py`) qui expose une API simple (`http://localhost:5555/gate`) que le système embarqué peut interroger.

## Fonctionnalités
1. **Tableau de bord (Dashboard)** : Statistiques en temps réel (nombre de clients, paiements du mois, entrées du jour) et historique récent.
2. **Caméra et Détection** : Flux vidéo en direct avec détection automatique ou manuelle des plaques. Affichage du statut d'autorisation et envoi du signal à la barrière.
3. **Gestion des Clients** : Ajouter, modifier, supprimer et rechercher des clients avec prise en charge du format des plaques d'immatriculation marocaines (ex: 78904 - ه - 6).
4. **Gestion des Paiements** : Enregistrer les paiements mensuels des clients via un sélecteur d'année et de mois.
5. **Historique des Accès (Logs)** : Journal complet de toutes les tentatives d'accès avec horodatage, statut et action de la barrière.

### Installation et Utilisation
1. Assurez-vous d'avoir Python 3.10+ installé.
2. Installez les dépendances requises :
   ```bash
   pip install -r requirements.txt
   ```
3. Placez votre modèle YOLO entraîné (`best.pt`) dans le dossier `model/`.
4. Lancez l'application :
   ```bash
   python main.py
   ```
