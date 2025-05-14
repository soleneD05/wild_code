import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

# Définition des tâches avec leurs périodes
detailed_phases = [
    ("Phase 1 : Définition des besoins", datetime(2025, 1, 1), datetime(2025, 1, 15)),
    ("Phase 1 : Choix des technologies", datetime(2025, 1, 15), datetime(2025, 1, 30)),
    ("Phase 1 : Architecture", datetime(2025, 2, 1), datetime(2025, 2, 15)),
    ("Phase 2 : Collecte des données", datetime(2025, 2, 15), datetime(2025, 3, 15)),
    ("Phase 2 : Développement du modèle", datetime(2025, 3, 15), datetime(2025, 4, 15)),
    ("Phase 2 : Entraînement", datetime(2025, 4, 15), datetime(2025, 5, 15)),
    ("Phase 3 : Conception du chatbot", datetime(2025, 5, 15), datetime(2025, 6, 15)),
    ("Phase 3 : Implémentation du moteur de recherche", datetime(2025, 6, 15), datetime(2025, 7, 15)),
    ("Phase 4 : Tests de performance", datetime(2025, 7, 15), datetime(2025, 8, 1)),
    ("Phase 4 : Tests fonctionnels", datetime(2025, 8, 1), datetime(2025, 8, 15)),
    ("Phase 4 : Tests utilisateurs", datetime(2025, 8, 15), datetime(2025, 9, 1)),
    ("Phase 4 : Tests de sécurité", datetime(2025, 9, 1), datetime(2025, 9, 15)),
    ("Phase 5 : Lancement officiel", datetime(2025, 9, 15), datetime(2025, 10, 1)),
    ("Phase 5 : Suivi des retours", datetime(2025, 10, 1), datetime(2025, 10, 15)),
    ("Phase 5 : Marketing", datetime(2025, 10, 15), datetime(2025, 10, 30)),
]

# Création du diagramme de Gantt
fig, ax = plt.subplots(figsize=(14, 8))
for i, (task, start, end) in enumerate(reversed(detailed_phases)):
    ax.barh(task, (end - start).days, left=start, color="orange", edgecolor="black")
    ax.text(start + (end - start) / 2, len(detailed_phases) - i - 1, 
            task.split(" : ")[1], ha="center", va="center", color="black", fontsize=9)

# Formatage des axes
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
plt.xticks(rotation=45, fontsize=10)
plt.yticks(fontsize=9)

# Ajout de titres et étiquettes
ax.set_xlabel("Timeline (Months)", fontsize=12)
ax.set_ylabel("Tasks", fontsize=12)
ax.set_title("Detailed Gantt Chart: PARIS FOOD Project", fontsize=14)

plt.tight_layout()
plt.show()
