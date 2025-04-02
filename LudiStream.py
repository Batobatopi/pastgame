import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import base64
from streamlit_option_menu import option_menu


st.set_page_config(page_title="PAST GAME", page_icon="🎲", layout="wide") #Pierre
# Fonction pour convertir l'image en base64
def img_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

    

chemin_logo = "Logo Past Game.png" #Pierre
# Le st.cache_data sert pour éviter les warnings sur Streamlit
# Charger les informations de vignettes depuis le fichier CSV local avec un encodage UTF-8
@st.cache_data
def load_image_data():
    try:
        # Charger avec l'encodage UTF-8 pour éviter les problèmes de caractères spéciaux
        df_images = pd.read_csv("bgg_thumbnail.csv", encoding = 'utf-8')
        return df_images
    except FileNotFoundError:
        st.error("Le fichier des images n'a pas été trouvé.")
        return pd.DataFrame()  # Retourner un DataFrame vide en cas d'erreur
    except UnicodeDecodeError:
        st.error("Erreur d'encodage avec le fichier des images.")
        return pd.DataFrame()  # Retourner un DataFrame vide en cas d'erreur d'encodage

df0 = pd.read_csv('bdd_bgg.csv', encoding = 'utf-8')
df1 = pd.read_csv('bgg_thumbnail.csv', encoding = 'utf-8')
df1 = df1[['id','Thumbnail']]
df = pd.merge(df0, df1, on = 'id', how = 'left')

df_images = load_image_data()  # Charger les images

# Vérification que df_images est bien chargé
if df_images.empty:
    st.stop()  # Arrêter l'exécution si les images ne sont pas disponibles

# On trie les jeux par ordre de note (plus haute vers la plus basse)
df_sorted = df.sort_values(by = 'bayesaverage', ascending = False)

# Nombre de jeux par page
games_per_page = 25

# Nombre total de pages
total_pages = len(df_sorted) // games_per_page + (1 if len(df_sorted) % games_per_page != 0 else 0)


# 🏠 MENU DE NAVIGATION
with st.sidebar:
    st.image(chemin_logo, width=250)  # Affiche le logo dans la barre latérale

    selection = option_menu(
        menu_title="Menu",        
        options=["Catalogue", "Recommandations"],  
        icons=["house", "search"],  
        menu_icon="cast",          
        default_index=0            
    )
# st.sidebar.image(chemin_logo, width=250)  # Pierre => mettre le logo dans la barre latérale
# ➞ PAGE CATALOGUE
if selection == "Catalogue":
    # Zone de saisie pour la recherche de jeu
    df['search_display'] = df['name'] + " (" + df['yearpublished'].astype(str) + ")" #Pierre
    game_name_filter = st.sidebar.selectbox("Recherchez un nom de jeu :",[""]+list(df['search_display'])) #Pierre

    # Double slider pour le nombre de joueurs (min)
    players_filter_min = st.sidebar.slider("Sélectionner le nombre de joueurs minimum", 1, 10, (1, 10))

    # Double slider pour le nombre de joueurs (max)
    players_filter_max = st.sidebar.slider("Sélectionner le nombre de joueurs maximum", 1, 10, (1, 10))

    # Slider pour la complexité
    complexity_filter = st.sidebar.slider("Sélectionner la complexité", 1, 5, (1, 5))

    # Filtre par mécanique
    mechanic_filter = st.sidebar.selectbox("Sélectionner la mécanique", ['Tous'] + sorted(df['Mecaniques'].dropna().unique().tolist()))

    # Filtre par lettre (Tous, A-E, F-J, K-O, P-T, U-Z, Autres)
    letter_filter = st.sidebar.selectbox("Sélectionner la plage de lettres", ['Tous', 'A - E', 'F - J', 'K - O', 'P - T', 'U - Z', 'Autres'])

    # Filtre de page
    page = st.sidebar.number_input("Page", min_value = 1, max_value = (len(df) // games_per_page + 1), step = 1, value = 1)

    # Fonction de filtrage en fonction de la plage de lettres sélectionnée
    def filter_by_letter_range(letter_filter):
        if letter_filter != 'Tous' and letter_filter != 'Autres':
            start_letter, end_letter = letter_filter.split(' - ')
            filtered_df = df_sorted[df_sorted['name'].str[0].between(start_letter, end_letter)]
        elif letter_filter == 'Autres':
            filtered_df = df_sorted[~df_sorted['name'].str[0].between('A', 'Z')]
        else:
            filtered_df = df_sorted
        return filtered_df

    # Appliquer le filtre par lettre
    filtered_df = filter_by_letter_range(letter_filter)

    # Appliquer un filtre de nombre de joueurs min
    filtered_df = filtered_df[(filtered_df['Min_joueurs'] >= players_filter_min[0]) & (filtered_df['Min_joueurs'] <= players_filter_min[1])]

    # Appliquer un filtre de nombre de joueurs max
    filtered_df = filtered_df[(filtered_df['Max_joueurs'] >= players_filter_max[0]) & (filtered_df['Max_joueurs'] <= players_filter_max[1])]

    # Appliquer le filtre par mécanique
    if mechanic_filter != 'Tous':
        filtered_df = filtered_df[filtered_df['Mecaniques'].str.contains(mechanic_filter, case=False, na = False)]

    # Appliquer le filtre de complexité avec le slider
    filtered_df = filtered_df[(filtered_df['Complexite'] >= complexity_filter[0]) & (filtered_df['Complexite'] <= complexity_filter[1])]

    # Si un nom de jeu a été entré, on ne prend pas en compte le filtrage par lettre ou joueurs
    if game_name_filter:
        filtered_df = df[df['search_display'] == game_name_filter ]

    # Calculer le début et la fin des jeux à afficher pour cette page
    start_idx = (page - 1) * games_per_page
    end_idx = min(page * games_per_page, len(filtered_df))

    # Sélectionner les jeux à afficher pour cette page
    games_to_display = filtered_df.iloc[start_idx:end_idx]

    # Affichage de la page actuelle pour la pagination
    st.write(f"Liste des jeux (Page {page} sur {len(filtered_df) // games_per_page + 1}):")
    for index, row in games_to_display.iterrows():
        st.header(f"{row['name']}")
        
        # Récupérer l'URL de l'image du jeu
        game_thumbnail_url = df_images[df_images['name'] == row['name']]['Thumbnail'].values
        if len(game_thumbnail_url) > 0:
            game_thumbnail_url = game_thumbnail_url[0]
        else:
            game_thumbnail_url = "https://via.placeholder.com/200"  # Image par défaut si pas trouvé
        
        # Affichage de l'image sous le titre du jeu
        st.markdown(f'<img src = "{game_thumbnail_url}" width = "200">', unsafe_allow_html=True)
        
        st.write(f"**Note** : {round(row['bayesaverage'], 2)}")

        # Utilisation de st.expander pour rendre le graphique caché au départ et ajouter des détails
        with st.expander(f"Détails pour {row['name']}"):
            st.write(f"**Année de sortie** : {row['yearpublished']}")
            st.write(f"**Mecaniques** : {row['Mecaniques']}")  # Correction ici
            
            # Vérifier si la catégorie existe et l'afficher, sinon indiquer "Non spécifié"
            category = row['Categories'] if 'Categories' in row and pd.notna(row['Categories']) else 'Non spécifié'
            st.write(f"**Catégorie** : {category}")

            # Affichage du nombre de joueurs min et max
            st.write(f"**Nombre de joueurs** : {row['Min_joueurs']} - {row['Max_joueurs']}")

            # Affichage de la complexité avec 2 chiffres après la virgule
            st.write(f"**Complexité** : {round(row['Complexite'], 2)}")


            if row['Francais'] == 'Yes' :
                st.write(f"🔵⚪🔴 Existe en version française")
            else : 
                st.write(f"❌ Pas de version française")
            
            st.markdown(f"[🔗 Voir sur BGG](https://boardgamegeek.com/boardgame/{row['id']})")

            # Transformation et normalisation des données durée (0-1)
            if row["Duree_moy"] <= 30:
                duration = 0  # 0h
            elif row["Duree_moy"] <= 60:
                duration = 1  # 1h
            elif row["Duree_moy"] <= 120:
                duration = 2  # 2h
            elif row["Duree_moy"] <= 180:
                duration = 3  # 3h
            else:
                duration = 4  # +3h

            duration_norm = duration / 4  # Normalisation sur [0,1]

            # Calcul de la moyenne entre Min_joueurs et Max_joueurs
            moyenne_joueurs = (row["Min_joueurs"] + row["Max_joueurs"]) / 2

            # Transformation et normalisation des données nb joueurs (0-1)
            if moyenne_joueurs <= 2:
                nbjoueur = 1  # <=2
            elif moyenne_joueurs <= 4:
                nbjoueur = 2  # <=4
            elif moyenne_joueurs <= 8:
                nbjoueur = 3  # <=8
            else:
                nbjoueur = 4  # >8

            nbjoueur_norm = nbjoueur / 4  # Normalisation sur [0,1]

            # Vérification des valeurs pour éviter les erreurs
            complexite = row.get("Complexite", 1)  # Valeur par défaut 1 si manquante
            bayesaverage = row.get("bayesaverage", 1)  # Valeur par défaut 1 si manquante

            complexite_norm = min(complexite, 5) / 5  # Normalisation sur [0,1]
            bayesaverage_norm = min(bayesaverage, 10) / 10  # Normalisation sur [0,1]

            # Création des données pour le graphique
            radar_data = {
                'Critère': ["Nombre de joueurs en moyenne", "Durée de jeu", "Complexité", "Notes"],
                'Valeur': [nbjoueur_norm, duration_norm, complexite_norm, bayesaverage_norm]
            }

            # Création du graphique en toile
            fig = go.Figure(data=go.Scatterpolar(
                r=radar_data['Valeur'],
                theta=radar_data['Critère'],
                fill="toself",
                name=row["name"]
            ))

            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 1]  # Échelle uniforme 0-1
                    )
                ),
                showlegend=False,
                title=f"Graphique en toile pour {row['name']}",
                width=333,
                height=333
            )

            # Afficher le graphique en toile d'araignée sous chaque jeu
            st.plotly_chart(fig)

    # Contrôles de navigation entre les pages
    col1, col2 = st.columns([1, 1])
    with col1:
        if page > 1:
            if st.button("Page précédente"):
                page -= 1
    with col2:
        if page < (len(filtered_df) // games_per_page + 1):
            if st.button("Page suivante"):
                page += 1





elif selection == "Recommandations":
    st.title("🔍 Recherche de jeux : ")
    # Zone de saisie pour la recherche de jeu
    df['search_display'] = df['name'] + " (" + df['yearpublished'].astype(str) + ")"
    search_query = st.selectbox("Recherchez un nom de jeu :",[""]+list(df['search_display']))
    if search_query != "":
        jeu_principal = df[df['search_display'] == search_query].iloc[0]
        st.markdown("🎲 Le jeu que vous avez sélectionné : ")
        col1, col2 = st.columns([1, 2])

        with col1:
            st.image(df[df['search_display'] == search_query]['Image'].values[0], width=450)

        with col2:
            st.write(f"🃏 Titre : {df[df['search_display'] == search_query]['name'].values[0]} ({df[df['search_display'] == search_query]['yearpublished'].values[0]})")
            st.write(f"⭐ Note moyenne : {round(df[df['search_display'] == search_query]['average'].values[0],1)}")
            st.write(f"🕑 Durée : {df[df['search_display'] == search_query]['Duree_moy'].values[0]} minutes")
            st.write(f"🎮 Nb joueurs : {df[df['search_display'] == search_query]['Min_joueurs'].values[0]}-{df[df['search_display'] == search_query]['Max_joueurs'].values[0]}")
            st.write(f"🎯 Mécaniques : {df[df['search_display'] == search_query]['Mecaniques'].values[0]}")
            st.write(f"♟️ Description : {df[df['search_display'] == search_query]['Description'].values[0]}")
            bgg_url = f" https://boardgamegeek.com/boardgame/{jeu_principal['id']}"
            st.write(f"➡️ Pour plus d'informations 🔗 [Voir sur BGG]({bgg_url})")
        

        st.markdown("---")



        # Charger les recommandations précalculées
        df_recommendations = pd.read_csv("reco_precalc.csv", index_col=0)

        # Vérifier si le jeu principal a des recommandations
        if jeu_principal['id'] in df_recommendations.index:
            recommended_games = df_recommendations.loc[jeu_principal['id']]
            
            max_games = 15  # Max de jeux affichés (3x5)
            games_list = list(recommended_games.items())[:max_games]  # Limiter à 15 jeux
            
            # Affichage structuré en lignes de 3 colonnes
            for row in range(0, len(games_list), 3):
                cols = st.columns(3)  # Créer une ligne avec 3 colonnes
                
                for i in range(3):  # Remplir chaque colonne
                    if row + i < len(games_list):  # Vérifier s'il reste des jeux à afficher
                        col_name, recommended_game_id = games_list[row + i]

                        # Vérifier si le jeu recommandé est dans le DataFrame principal
                        game_info = df[df.index == recommended_game_id]
                        if not game_info.empty:
                            game_info = game_info.iloc[0]  # Sélectionner la première ligne

                            with cols[i]:  # Insérer le jeu dans la bonne colonne
                                if pd.isna(game_info['Thumbnail']) or game_info['Thumbnail'] == '':
                                    st.image(chemin_logo, caption="Image non disponible", width= 150)
                                else:
                                    st.image(game_info['Thumbnail'])
                                st.write(f"**{game_info['name']} ({game_info['yearpublished']})**")
                                st.write(f"⭐ {round(game_info['average'], 1)}")

                                st.write(f" {game_info['Min_joueurs']}-{game_info['Max_joueurs']} joueurs")
                                st.write(f"🕑 {game_info['Duree_moy']} min")
                                if game_info['Francais'] == 'Yes' :
                                    st.write(f"🔵⚪🔴 Existe en version française")
                                else : 
                                    st.write(f"❌ Pas de version française")
                                st.markdown(f"[🔗 Voir sur BGG](https://boardgamegeek.com/boardgame/{game_info['id']})")

        else:
            st.warning("Aucune recommandation trouvée pour ce jeu.")    






