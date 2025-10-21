import streamlit as st
import pandas as pd
import numpy as np
from pymongo import MongoClient

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Recomendación de Películas",
    page_icon="🎬",
    layout="wide"
)

# Conexión a MongoDB
@st.cache_resource
def get_database_connection():
    try:
        client = MongoClient("mongodb+srv://juantovarg_db_user:USIL2025us@cluster0.45sx7fd.mongodb.net/")
        db = client["movie_recommendation_db"]
        return db, True
    except Exception as e:
        st.error(f"Error al conectar con MongoDB: {e}")
        return None

# Función para inicializar la base de datos con datos de ejemplo
def initialize_database(db):
    # Verificar si ya existen datos
    if db.movies.count_documents({}) == 0:
        # Datos de ejemplo de películas
        movies_data = [
            {
                "title": "El Padrino",
                "year": 1972,
                "director": "Francis Ford Coppola",
                "genres": ["Crimen", "Drama"],
                "description": "La historia de la familia mafiosa Corleone liderada por Don Vito Corleone.",
                "rating": 9.2
            },
            {
                "title": "Pulp Fiction",
                "year": 1994,
                "director": "Quentin Tarantino",
                "genres": ["Crimen", "Drama"],
                "description": "Varias historias entrelazadas de criminales en Los Ángeles.",
                "rating": 8.9
            },
            {
                "title": "La La Land",
                "year": 2016,
                "director": "Damien Chazelle",
                "genres": ["Musical", "Romance", "Drama"],
                "description": "Un pianista de jazz y una aspirante a actriz se enamoran en Los Ángeles.",
                "rating": 8.0
            },
            {
                "title": "El Señor de los Anillos: La Comunidad del Anillo",
                "year": 2001,
                "director": "Peter Jackson",
                "genres": ["Aventura", "Fantasía"],
                "description": "Un hobbit debe destruir un anillo poderoso para salvar a la Tierra Media.",
                "rating": 8.8
            },
            {
                "title": "Interestelar",
                "year": 2014,
                "director": "Christopher Nolan",
                "genres": ["Ciencia Ficción", "Aventura", "Drama"],
                "description": "Astronautas viajan a través de un agujero de gusano para salvar a la humanidad.",
                "rating": 8.6
            },
            {
                "title": "Ciudad de Dios",
                "year": 2002,
                "director": "Fernando Meirelles",
                "genres": ["Crimen", "Drama"],
                "description": "La historia del crecimiento del crimen organizado en los suburbios de Río de Janeiro.",
                "rating": 8.6
            },
            {
                "title": "El Laberinto del Fauno",
                "year": 2006,
                "director": "Guillermo del Toro",
                "genres": ["Fantasía", "Drama", "Guerra"],
                "description": "En la España de posguerra, una niña descubre un mundo fantástico.",
                "rating": 8.2
            },
            {
                "title": "Guardianes de la Galaxia",
                "year": 2014,
                "director": "James Gunn",
                "genres": ["Acción", "Aventura", "Ciencia Ficción"],
                "description": "Un grupo de criminales intergalácticos se une para salvar la galaxia.",
                "rating": 8.0
            },
            {
                "title": "Coco",
                "year": 2017,
                "director": "Lee Unkrich",
                "genres": ["Animación", "Aventura", "Familiar"],
                "description": "Un niño viaja al mundo de los muertos para descubrir secretos familiares.",
                "rating": 8.4
            },
            {
                "title": "El Caballero de la Noche",
                "year": 2008,
                "director": "Christopher Nolan",
                "genres": ["Acción", "Crimen", "Drama"],
                "description": "Batman se enfrenta al Joker, un criminal que busca el caos en Gotham City.",
                "rating": 9.0
            }
        ]

        # Insertar datos en la colección de películas
        db.movies.insert_many(movies_data)

        # Datos de ejemplo de usuarios
        users_data = [
            {
                "username": "usuario1",
                "password": "usuario1",  # En una app real, esto debería estar encriptado
                "favorites": ["El Padrino", "Pulp Fiction"],
                "preferred_genres": ["Crimen", "Drama"]
            },
            {
                "username": "usuario2",
                "password": "usuario2",
                "favorites": ["La La Land", "Coco"],
                "preferred_genres": ["Musical", "Animación", "Familiar"]
            },
            {
                "username": "usuario3",
                "password": "usuario3",
                "favorites": ["El Señor de los Anillos: La Comunidad del Anillo", "Interestelar"],
                "preferred_genres": ["Aventura", "Ciencia Ficción", "Fantasía"]
            }
        ]

        # Insertar datos en la colección de usuarios
        db.users.insert_many(users_data)
        return True
    return False

# Función para obtener todas las películas
def get_all_movies(db):
    movies = list(db.movies.find({}, {"_id": 0}))
    return movies

# Función para obtener las películas favoritas de un usuario
def get_user_favorites(db, username):
    user = db.users.find_one({"username": username})
    if user and "favorites" in user:
        favorite_movies = []
        for title in user["favorites"]:
            movie = db.movies.find_one({"title": title}, {"_id": 0})
            if movie:
                favorite_movies.append(movie)
        return favorite_movies
    return []

# Función para obtener recomendaciones basadas en contenido
def get_content_based_recommendations(db, username, n_recommendations=5):
    # Obtener el usuario
    user = db.users.find_one({"username": username})
    if not user or "preferred_genres" not in user:
        return []

    # Obtener las preferencias del usuario
    preferred_genres = user["preferred_genres"]

    # Obtener todas las películas
    all_movies = get_all_movies(db)

    # Crear una función de puntuación para cada película según los géneros favoritos
    def score_movie(movie):
        score = 0
        for genre in movie["genres"]:
            if genre in preferred_genres:
                score += 1
        return score * (movie["rating"] / 10)  # Normalizar por calificación

    # Calificar y ordenar películas
    scored_movies = [(movie, score_movie(movie)) for movie in all_movies]
    scored_movies.sort(key=lambda x: x[1], reverse=True)

    # Filtrar las películas que ya están en favoritos
    favorites = user.get("favorites", [])
    recommendations = [movie for movie, score in scored_movies if movie["title"] not in favorites]

    return recommendations[:n_recommendations]

# Función para autenticar usuario
def authenticate_user(db, username, password):
    user = db.users.find_one({"username": username, "password": password})
    return user is not None

# Función para agregar una película a favoritos
def add_to_favorites(db, username, movie_title):
    # Actualizar lista de favoritos del usuario
    db.users.update_one(
        {"username": username},
        {"$addToSet": {"favorites": movie_title}}
    )

# Función para verificar si una película está en favoritos
def is_favorite(db, username, movie_title):
    user = db.users.find_one({"username": username})
    if user and "favorites" in user:
        return movie_title in user["favorites"]
    return False

# Función para mostrar las tarjetas de películas
def display_movie_cards(movies, db=None, flag=None, username=None, show_favorite_button=False):
    cols = st.columns(3)

    for i, movie in enumerate(movies):
        with cols[i % 3]:
            st.markdown(f"""
            <div style="border:1px solid #ddd; padding:10px; border-radius:5px; margin-bottom:10px">
                <h3>{movie['title']} ({movie['year']})</h3>
                <p><strong>Director:</strong> {movie['director']}</p>
                <p><strong>Géneros:</strong> {', '.join(movie['genres'])}</p>
                <p><strong>Calificación:</strong> {movie['rating']}/10</p>
                <p>{movie['description']}</p>
            </div>
            """, unsafe_allow_html=True)

            if show_favorite_button and flag and username:
                is_fav = is_favorite(db, username, movie['title'])
                if is_fav:
                    st.button("✅ En Favoritos", key=f"fav_{i}", disabled=True)
                else:
                    if st.button("Añadir a favoritos", key=f"fav_{i}"):
                        add_to_favorites(db, username, movie['title'])
                        st.rerun()

# Función principal
def main():
    st.title("Sistema de Recomendación de Películas")

    # Conectar a la base de datos
    db, flag = get_database_connection()
    if not flag:
        st.error("No se pudo conectar a la base de datos")
        return

    # Inicializar la base de datos si es necesario
    if initialize_database(db):
        st.success("Base de datos inicializada con datos de ejemplo")

    # Gestión de sesiones
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""

    # Interfaz de inicio de sesión
    if not st.session_state.logged_in:
        st.subheader("Iniciar Sesión")

        col1, col2 = st.columns(2)

        with col1:
            username = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")

            if st.button("Iniciar Sesión"):
                if authenticate_user(db, username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos")

        with col2:
            st.info("""
            ### Usuarios de prueba:
            - **Usuario 1**: usuario1 / usuario1
            - **Usuario 2**: usuario2 / usuario2
            - **Usuario 3**: usuario3 / usuario3
            """)

    # Interfaz principal (usuario logueado)
    else:
        st.sidebar.title(f"Bienvenido, {st.session_state.username}")

        if st.sidebar.button("Cerrar Sesión"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()

        # Crear pestañas para organizar el contenido
        tab1, tab2, tab3 = st.tabs(["Recomendaciones", "Películas Favoritas", "Todas las Películas"])

        # Pestaña de recomendaciones
        with tab1:
            st.header("Recomendaciones para Ti")
            recommendations = get_content_based_recommendations(db, st.session_state.username)

            if recommendations:
                display_movie_cards(recommendations, db, flag, st.session_state.username, True)
            else:
                st.info("No hay recomendaciones disponibles en este momento.")

        # Pestaña de favoritos
        with tab2:
            st.header("Tus Películas Favoritas")
            favorites = get_user_favorites(db, st.session_state.username)

            if favorites:
                display_movie_cards(favorites, flag=flag)
            else:
                st.info("No tienes películas favoritas aún.")

        # Pestaña de todas las películas
        with tab3:
            st.header("Catálogo Completo")
            all_movies = get_all_movies(db)
            display_movie_cards(all_movies, db, st.session_state.username, True)

            # Añadir un filtro por género
            with st.expander("Filtrar por Género"):
                # Obtener todos los géneros únicos
                all_genres = set()
                for movie in all_movies:
                    for genre in movie["genres"]:
                        all_genres.add(genre)

                selected_genres = st.multiselect("Selecciona géneros", sorted(all_genres))

                if selected_genres:
                    filtered_movies = [
                        movie for movie in all_movies
                        if any(genre in selected_genres for genre in movie["genres"])
                    ]

                    st.subheader("Películas Filtradas")
                    display_movie_cards(filtered_movies, db, st.session_state.username, True)

if __name__ == "__main__":
    main()
