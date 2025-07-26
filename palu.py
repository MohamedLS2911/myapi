# dashboard_app.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import re
from io import BytesIO

st.set_page_config(page_title="Tableau de bord Paludisme", layout="wide")
st.sidebar.title("📌 Navigation")

# Menu principal
menu = st.sidebar.selectbox("Choisir une section", [
    "Accueil",
    "Analyse par indicateur",
    "Carte interactive",
    "Comparaison temporelle",
    "Téléchargements"
])


# Chargement et cache des données
@st.cache_data
def load_data():
    df = pd.read_csv("data.csv")
    df.columns = df.columns.str.strip()
    return df


df = load_data()

# Colonnes non analytiques
meta_cols = ['organisationunitid', 'organisationunitname', 'organisationunitcode', 'organisationunitdescription']
value_columns = [col for col in df.columns if col not in meta_cols]

# Extraction des indicateurs
indicateurs_dict = {}
for col in value_columns:
    match = re.match(
        r"(.*?) (Janvier|Février|Mars|Avril|Mai|Juin|Juillet|Août|Septembre|Octobre|Novembre|Décembre) (\d{4}) (.*)",
        col)
    if match:
        indicateur = match.group(1).strip()
        mois = f"{match.group(2)} {match.group(3)}"
        structure = match.group(4).strip()
        if indicateur not in indicateurs_dict:
            indicateurs_dict[indicateur] = []
        indicateurs_dict[indicateur].append((mois, structure, col))

# Page Accueil
if menu == "Accueil":
    st.title("🏠 Tableau de bord Paludisme")
    st.markdown("""
    Bienvenue dans le tableau de bord interactif pour l'analyse des données de paludisme.

    Ce tableau permet de :
    - Visualiser les indicateurs clés par mois et par type de structure
    - Afficher les cas par arrondissement
    - Exporter les tableaux en Excel
    - Explorer les données sur une carte interactive (si coordonnées disponibles)

    _Sources des données : DHIS2, rapports des structures sanitaires_
    """)

# Page Analyse par indicateur
elif menu == "Analyse par indicateur":
    st.title("📈 Analyse par indicateur")

    indicateur_choisi = st.selectbox("Indicateur", sorted(indicateurs_dict.keys()))
    options_mois = sorted(set(mois for mois, _, _ in indicateurs_dict[indicateur_choisi]))
    mois_choisi = st.selectbox("Mois", options_mois)
    options_structures = sorted(
        set(structure for mois, structure, _ in indicateurs_dict[indicateur_choisi] if mois == mois_choisi))
    structure_choisie = st.selectbox("Type de structure", options_structures)

    colonne_finale = None
    for mois, structure, col in indicateurs_dict[indicateur_choisi]:
        if mois == mois_choisi and structure == structure_choisie:
            colonne_finale = col
            break

    if colonne_finale:
        st.subheader(f"{indicateur_choisi} - {mois_choisi} ({structure_choisie})")
        df_viz = df[['organisationunitname', colonne_finale]].dropna()
        df_viz[colonne_finale] = pd.to_numeric(df_viz[colonne_finale], errors='coerce')
        df_viz = df_viz.sort_values(by=colonne_finale, ascending=False)

        st.dataframe(df_viz)

        buffer = BytesIO()
        df_viz.to_excel(buffer, index=False, engine='xlsxwriter')
        buffer.seek(0)
        st.download_button(
            label="📥 Télécharger ce tableau (Excel)",
            data=buffer,
            file_name=f"{indicateur_choisi}_{mois_choisi}_{structure_choisie}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        fig, ax = plt.subplots(figsize=(12, 5))
        ax.bar(df_viz['organisationunitname'], df_viz[colonne_finale], color='darkblue')
        ax.set_ylabel("Nombre de cas")
        ax.set_title(f"{indicateur_choisi} ({structure_choisie}) - {mois_choisi}")
        ax.set_xticks(range(len(df_viz)))
        ax.set_xticklabels(df_viz['organisationunitname'], rotation=90)
        st.pyplot(fig)

# Carte interactive
elif menu == "Carte interactive":
    st.title("🗺️ Carte interactive des cas")
    if 'latitude' in df.columns and 'longitude' in df.columns:
        df_map = df.dropna(subset=['latitude', 'longitude'])
        df_map['latitude'] = pd.to_numeric(df_map['latitude'], errors='coerce')
        df_map['longitude'] = pd.to_numeric(df_map['longitude'], errors='coerce')
        st.map(df_map[['latitude', 'longitude']])
    else:
        st.warning("Les colonnes latitude et longitude sont absentes du fichier.")

# Comparaison temporelle (à développer)
elif menu == "Comparaison temporelle":
    st.title("📊 Comparaison temporelle des cas")
    st.info("Module en cours de développement. Prévu : évolution mensuelle ou trimestrielle par structure.")

# Téléchargements multiples (à développer)
elif menu == "Téléchargements":
    st.title("📥 Téléchargement des fichiers")
    st.info("Téléchargement groupé ou personnalisé des fichiers sera bientôt disponible.")
