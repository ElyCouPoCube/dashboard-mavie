import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import matplotlib.pyplot as plt

# Téléchargement des fichiers
uploaded_files = {
    'inscription': st.file_uploader("Télécharger le fichier des inscriptions", type="xlsx"),
    'foyer': st.file_uploader("Télécharger le fichier des foyers", type="xlsx"),
    'individu': st.file_uploader("Télécharger le fichier des individus", type="xlsx"),
    'accident': st.file_uploader("Télécharger le fichier des accidents", type="xlsx")
}

if all(uploaded_files.values()):
    # Chargement des données
    dfs = {name: pd.read_excel(file) for name, file in uploaded_files.items()}

    # Calcul de l'année actuelle
    current_year = pd.Timestamp.now().year

    # Onglets pour chaque catégorie d'analyse
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Suivi des volontaires", "Données des volontaires", "Données des accidents", "Facteurs de risques", "Corrélation des accidents"])

    with tab1:
        st.header("Suivi des volontaires")

        # Analyse des inscriptions par mois
        df_inscriptions_par_mois = dfs['inscription'].copy()
        df_inscriptions_par_mois['DATE DE REMPLISSAGE'] = pd.to_datetime(df_inscriptions_par_mois['DATE DE REMPLISSAGE'], errors='coerce').dt.to_period("M")
        inscriptions_par_mois = df_inscriptions_par_mois.groupby('DATE DE REMPLISSAGE').size().reset_index(name='Nombre d\'inscriptions')
        inscriptions_par_mois['DATE DE REMPLISSAGE'] = inscriptions_par_mois['DATE DE REMPLISSAGE'].dt.to_timestamp()
        
        fig_inscriptions = px.line(inscriptions_par_mois, x='DATE DE REMPLISSAGE', y='Nombre d\'inscriptions', title="Évolution des inscriptions au fil du temps")
        st.plotly_chart(fig_inscriptions)

        # Analyse de la rétention des volontaires
        st.subheader("Rétention des volontaires")
        retention_rate = len(dfs['individu']['VOLONTAIRE N°'].unique()) / len(dfs['inscription']['VOLONTAIRE N°'].unique()) * 100
        st.metric(label="Taux de rétention", value=f"{retention_rate:.2f}%")

        # Distribution de l'âge des volontaires au moment de l'inscription
        df_inscriptions_par_mois['ANNEE DE NAISSANCE'] = pd.to_numeric(df_inscriptions_par_mois['ANNEE DE NAISSANCE'].str.extract(r'(\d{4})')[0], errors='coerce')
        df_inscriptions_par_mois['AGE_INSCRIPTION'] = current_year - df_inscriptions_par_mois['ANNEE DE NAISSANCE']
        fig_age_inscription = px.histogram(df_inscriptions_par_mois, x='AGE_INSCRIPTION', nbins=20, title="Distribution de l'âge des volontaires au moment de l'inscription")
        st.plotly_chart(fig_age_inscription)

    with tab2:
        st.header("Analyse des données des volontaires")

        # Analyse de la répartition par genre
        fig_genre = px.pie(dfs['individu'], names='GENRE', title="Répartition des volontaires par genre")
        st.plotly_chart(fig_genre)

                # Analyse de la répartition par âge
        dfs['individu']['ANNEE DE NAISSANCE'] = pd.to_numeric(dfs['individu']['ANNEE DE NAISSANCE'].str.extract(r'(\d{4})')[0], errors='coerce')
        dfs['individu'] = dfs['individu'].dropna(subset=['ANNEE DE NAISSANCE'])
        dfs['individu']['AGE'] = current_year - dfs['individu']['ANNEE DE NAISSANCE']
    
        age_bins = [0, 18, 30, 40, 50, 60, 70, 80, 100]
        dfs['individu']['TRANCHE_AGE'] = pd.cut(dfs['individu']['AGE'], bins=age_bins, labels=["0-17", "18-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"])
    
        # Nouveau code pour histogramme décroissant
        fig_age = px.histogram(dfs['individu'], x='TRANCHE_AGE', title="Répartition des volontaires par tranche d'âge", category_orders={'TRANCHE_AGE': dfs['individu']['TRANCHE_AGE'].value_counts().index.tolist()})
        st.plotly_chart(fig_age)
    
               # Calculer la répartition par niveau d'éducation
        diplome_counts = dfs['individu']['Quel est le diplôme le plus élevé que vous avez obtenu ?'].value_counts()

        # Créer l'histogramme décroissant
        fig_diplome = px.bar(
            diplome_counts.sort_values(ascending=False),
            x=diplome_counts.index,
            y=diplome_counts.values,
            title="Répartition par niveau d'éducation",
            labels={'x': 'Niveau d\'éducation', 'y': 'Nombre de volontaires'}
        )

        st.plotly_chart(fig_diplome)


        # Analyse de la situation professionnelle
        fig_situation_emploi = px.pie(dfs['individu'], names='Quelle est votre situation actuelle par rapport à l\'emploi ?', title="Répartition par situation professionnelle")
        st.plotly_chart(fig_situation_emploi)

        # Calculer la répartition par lieu de résidence en excluant les valeurs nulles
        lieu_residence_counts = dfs['foyer']['Votre lieu de résidence se trouve en :'].dropna().value_counts()

        # Créer l'histogramme décroissant
        fig_lieu_residence = px.bar(
            lieu_residence_counts.sort_values(ascending=False),
            x=lieu_residence_counts.index,
            y=lieu_residence_counts.values,
            title="Répartition des volontaires par lieu de résidence",
            labels={'x': 'Lieu de résidence', 'y': 'Nombre de volontaires'}
        )

        st.plotly_chart(fig_lieu_residence)

    with tab3:
        st.header("Analyse des données des accidents")

        # Répartition des accidents par type
        if 'De quel type d\'accident s\'agissait-il ?' in dfs['accident']:
            accident_types = dfs['accident']["De quel type d'accident s'agissait-il ?"].value_counts()
            accident_types_above_threshold = accident_types[accident_types >= 5]
            accident_types_below_threshold = pd.Series({'Autres': accident_types[accident_types < 5].sum()})
            accident_types = pd.concat([accident_types_above_threshold, accident_types_below_threshold])

            fig_accident_types = px.pie(accident_types, names=accident_types.index, values=accident_types.values, title="Répartition des types d'accidents")
            st.plotly_chart(fig_accident_types)
        else:
            st.warning("La colonne 'De quel type d'accident s'agissait-il ?' est manquante dans les données.")

        # Calculer la répartition des accidents par lieu en excluant les valeurs nulles
        accident_location_counts = dfs['accident']['Où a eu lieu l\'accident ?'].dropna().value_counts()

        # Créer l'histogramme décroissant
        fig_accident_location = px.bar(
            accident_location_counts.sort_values(ascending=False),
            x=accident_location_counts.index,
            y=accident_location_counts.values,
            title="Répartition des accidents par lieu",
            labels={'x': 'Lieu de l\'accident', 'y': 'Nombre d\'accidents'}
        )

        st.plotly_chart(fig_accident_location)

        # Analyse de la gravité des accidents
        if 'Combien de jours avez-vous été hospitalisé(e) ?' in dfs['accident']:
            accident_data = dfs['accident'].dropna(subset=['Combien de jours avez-vous été hospitalisé(e) ?'])
            accident_data['Gravité'] = accident_data["Combien de jours avez-vous été hospitalisé(e) ?"].apply(lambda x: 'Grave' if x > 3 else 'Léger')

            fig_gravite = px.pie(accident_data, names="Gravité", title="Répartition de la gravité des accidents")
            st.plotly_chart(fig_gravite)
        else:
            st.warning("La colonne sur les jours d'hospitalisation est manquante dans les données.")

        # Analyse des accidents par âge
        if 'ANNEE DE NAISSANCE' in dfs['accident']:
            accident_data_age = dfs['accident'].dropna(subset=['ANNEE DE NAISSANCE'])
            accident_data_age['AGE_ACCIDENT'] = current_year - pd.to_numeric(accident_data_age['ANNEE DE NAISSANCE'].str.extract(r'(\d{4})')[0], errors='coerce')
            accident_data_age = accident_data_age.dropna(subset=['AGE_ACCIDENT'])

            age_bins = [0, 18, 30, 40, 50, 60, 70, 80, 100]
            accident_data_age['TRANCHE_AGE_ACCIDENT'] = pd.cut(accident_data_age['AGE_ACCIDENT'], bins=age_bins, labels=["0-17", "18-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"])

            # Nouveau code pour histogramme décroissant
            fig_age_accident = px.histogram(accident_data_age, x='TRANCHE_AGE_ACCIDENT', title="Répartition des accidents par tranche d'âge", category_orders={'TRANCHE_AGE_ACCIDENT': accident_data_age['TRANCHE_AGE_ACCIDENT'].value_counts().index.tolist()})
            st.plotly_chart(fig_age_accident)
        else:
            st.warning("La colonne 'ANNEE DE NAISSANCE' est manquante dans les données.")

    with tab4:
        st.header("Analyse des facteurs de risques")

        # Calcul de l'IMC et suppression des valeurs nulles
        dfs['individu']['IMC'] = dfs['individu']["Quel est votre poids actuel en kg ?"] / (dfs['individu']["Quelle est votre taille actuelle en cm ?"] / 100) ** 2
        dfs['individu'] = dfs['individu'].dropna(subset=['IMC'])
        
        # Définir les tranches d'IMC
        imc_bins = [0, 18.5, 25, 30, 35, 40, 50]
        dfs['individu']['TRANCHE_IMC'] = pd.cut(dfs['individu']['IMC'], bins=imc_bins, labels=["Insuffisance pondérale", "Corpulence normale", "Surpoids", "Obésité modérée", "Obésité sévère", "Obésité morbide"])
        
        # Créer le camembert de la répartition par tranche d'IMC
        imc_counts = dfs['individu']['TRANCHE_IMC'].dropna().value_counts()
        
        fig_imc = px.pie(
            values=imc_counts.values,
            names=imc_counts.index,
            title="Répartition des volontaires par tranche d'IMC"
        )
        
        st.plotly_chart(fig_imc)

        # Retirer les valeurs nulles pour la consommation d'alcool
        alcool_counts = dfs['individu']["A quelle fréquence consommez-vous de l'alcool (Vin, bière, cidre,apéritif, digestif, …) ?"].dropna().value_counts()

        # Créer le camembert de la répartition de la consommation d'alcool
        fig_alcohol = px.pie(
            values=alcool_counts.values,
            names=alcool_counts.index,
            title="Répartition de la consommation d'alcool"
        )

        st.plotly_chart(fig_alcohol)

        # Analyse de la consommation de tabac
        if "Combien fumez-vous ou fumiez-vous de cigarettes, cigarillos, cigares ou pipes par jour ?" in dfs['individu']:
            tabac_data = dfs['individu'].dropna(subset=["Combien fumez-vous ou fumiez-vous de cigarettes, cigarillos, cigares ou pipes par jour ?"])
            fig_tabac = px.pie(tabac_data, names="Combien fumez-vous ou fumiez-vous de cigarettes, cigarillos, cigares ou pipes par jour ?", title="Répartition de la consommation de tabac")
            st.plotly_chart(fig_tabac)
        else:
            st.warning("La colonne 'Consommation de tabac' est manquante dans les données des individus.")

        # Analyse de la consommation de cannabis
        if "Avez-vous consommé du cannabis (haschisch, marijuana, herbe, joint, shit) au cours des 30 derniers jours ?" in dfs['individu']:
            cannabis_data = dfs['individu'].dropna(subset=["Avez-vous consommé du cannabis (haschisch, marijuana, herbe, joint, shit) au cours des 30 derniers jours ?"])
            fig_cannabis = px.pie(cannabis_data, names="Avez-vous consommé du cannabis (haschisch, marijuana, herbe, joint, shit) au cours des 30 derniers jours ?", 
                                  title="Répartition de la consommation de cannabis")
            st.plotly_chart(fig_cannabis)
        else:
            st.warning("La colonne 'Consommation de cannabis' est manquante dans les données des individus.")

        # Analyse des conditions physiques et mentales par rapport aux accidents
        if "Sur cette échelle de 1 à 10, en moyenne au cours de la semaine passée, comment vous êtes-vous senti sur le plan physique ?" in dfs['individu'] and "Sur cette échelle de 1 à 10, en moyenne au cours de la semaine passée, comment vous êtes-vous senti sur le plan mental ?" in dfs['individu']:
            fig_physical_mental = px.scatter(dfs['individu'], 
                                             x="Sur cette échelle de 1 à 10, en moyenne au cours de la semaine passée, comment vous êtes-vous senti sur le plan physique ?", 
                                             y="Sur cette échelle de 1 à 10, en moyenne au cours de la semaine passée, comment vous êtes-vous senti sur le plan mental ?", 
                                             color="Au cours des 12 derniers mois, avez-vous eu un ou des accidents ?", 
                                             title="Influence des conditions physiques et mentales sur les accidents")
            st.plotly_chart(fig_physical_mental)
        else:
            st.warning("Les colonnes sur l'état physique et mental sont manquantes dans les données des individus.")

        # Calculer la répartition des types d'habitat en excluant les valeurs nulles
        habitat_counts = dfs['foyer']['Quel est le type d\'habitat de votre voisinage ?'].dropna().value_counts()

        # Créer l'histogramme décroissant
        fig_habitat = px.bar(
            habitat_counts.sort_values(ascending=False),
            x=habitat_counts.index,
            y=habitat_counts.values,
            title="Répartition des types d'habitat",
            labels={'x': 'Type d\'habitat', 'y': 'Nombre de foyers'}
        )

        st.plotly_chart(fig_habitat)

        # Analyse des conditions de vie et accidents
        if "Parmi les tranches suivantes, dans laquelle se situe le revenu mensuel net de votre foyer ?" in dfs['foyer'] and "Combien de personnes vivent avec vous dans votre foyer ?" in dfs['foyer']:
            fig_conditions = px.scatter(dfs['foyer'], x="Parmi les tranches suivantes, dans laquelle se situe le revenu mensuel net de votre foyer ?", 
                                        y="Combien de personnes vivent avec vous dans votre foyer ?", 
                                        color="Avez-vous des animaux domestiques ?", 
                                        size="Quelle est la surface de votre logement ?", 
                                        title="Influence des conditions de vie sur les accidents")
            st.plotly_chart(fig_conditions)
        else:
            st.warning("Les colonnes sur le revenu ou le nombre de personnes dans le foyer sont manquantes dans les données des foyers.")

    with tab5:
        st.header("Analyse de la corrélation des accidents")

        # Corrélation entre différentes variables liées aux accidents
        numeric_columns = dfs['accident'].select_dtypes(include=['float64', 'int64']).columns
        correlation_matrix = dfs['accident'][numeric_columns].corr()

        fig_corr = plt.figure(figsize=(10, 8))
        sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0)
        st.pyplot(fig_corr)

else:
    st.warning("Veuillez télécharger tous les fichiers nécessaires pour commencer l'analyse.")
    
