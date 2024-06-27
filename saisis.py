import psycopg2
from datetime import date, timedelta
import PySimpleGUI as sg

visited_restaurants = set()

def is_resto_visited_this_week(resto_id):
    conn = None
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="portugal2.1",
            host="127.0.0.1",
            port="5432"
        )
        cursor = conn.cursor()

        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        cursor.execute("""
            SELECT COUNT(*)
            FROM visite
            WHERE id_restau = %s
            AND dt_visite BETWEEN %s AND %s
        """, (resto_id, start_of_week, end_of_week))

        count = cursor.fetchone()[0]
        return count > 0

    except psycopg2.Error as e:
        print(f"Erreur lors de la connexion à PostgreSQL ou de la recherche de la visite: {e}")
        return True  # Considérer qu'une visite existe en cas d'erreur

    finally:
        if conn:
            cursor.close()
            conn.close()

def get_cuisines():
    conn = None
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="portugal2.1",
            host="127.0.0.1",
            port="5432"
        )
        cursor = conn.cursor()

        cursor.execute("SELECT type_cuisine, libelle_cuisine FROM cuisine ORDER BY type_cuisine")
        cuisines = cursor.fetchall()
        return cuisines

    except psycopg2.Error as e:
        print(f"Erreur lors de la connexion à PostgreSQL: {e}")
        return []

    finally:
        if conn:
            cursor.close()
            conn.close()

def get_closest_resto(criteria):
    global visited_restaurants
    conn = None
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="portugal2.1",
            host="127.0.0.1",
            port="5432"
        )
        cursor = conn.cursor()

        query = "SELECT * FROM resto WHERE actif = 't'"
        params = []

        if 'cuisine' in criteria:
            query += " AND type_cuisine = %s"
            params.append(criteria['cuisine'])

        if 'price' in criteria:
            query += " AND prix <= %s"
            params.append(criteria['price'])

        if 'wait_time' in criteria:
            query += " AND service <= %s"
            params.append(criteria['wait_time'])

        if 'rating' in criteria:
            query += " AND satisfaction >= %s"
            params.append(criteria['rating'])

        query += " ORDER BY prix DESC"
        cursor.execute(query, tuple(params))

        restos = cursor.fetchall()

        if restos:
            unvisited_restos = [resto for resto in restos if resto[-1] not in visited_restaurants]
            if not unvisited_restos:
                return None, "Tous les restaurants disponibles ont été visités cette semaine."

            random_resto = unvisited_restos[0]  # Sélection du premier restaurant (prix le plus élevé)
            resto_id = random_resto[-1]  # Assurez-vous que l'ID du restaurant est bien le dernier champ
            visited_restaurants.add(resto_id)

            if not is_resto_visited_this_week(resto_id):
                return random_resto, None
            else:
                return get_closest_resto(criteria)  # Essayer à nouveau avec une autre sélection

        # Si aucun restaurant ne correspond exactement, essayer de trouver le plus proche
        closest_query = "SELECT * FROM resto WHERE actif = 't'"
        closest_params = []
        if 'cuisine' in criteria:
            closest_query += " AND type_cuisine = %s"
            closest_params.append(criteria['cuisine'])

        closest_query += " ORDER BY ABS(prix - %s), ABS(service - %s), ABS(satisfaction - %s)"
        closest_params.extend([criteria.get('price', 0), criteria.get('wait_time', 0), criteria.get('rating', 0)])

        cursor.execute(closest_query, tuple(closest_params))
        closest_restos = cursor.fetchall()

        if closest_restos:
            for resto in closest_restos:
                resto_id = resto[-1]
                if resto_id not in visited_restaurants and not is_resto_visited_this_week(resto_id):
                    visited_restaurants.add(resto_id)
                    return resto, None
            return None, "Tous les restaurants disponibles ont été visités cette semaine."
        else:
            return None, "Aucun restaurant disponible ne correspond aux critères."

    except psycopg2.Error as e:
        print(f"Erreur lors de la connexion à PostgreSQL: {e}")
        return None, "Erreur lors de la connexion à la base de données."

    finally:
        if conn:
            cursor.close()
            conn.close()

def main():
    global visited_restaurants

    cuisines = get_cuisines()
    cuisine_options = [f"{cuisine[0]}: {cuisine[1]}" for cuisine in cuisines]

    layout = [
        [sg.Text("Veuillez choisir deux critères parmi les suivants :", text_color='white', background_color='black', font=('Helvetica', 14))],
        [sg.Text(" ", size=(1, 2), background_color='black')],
        [sg.Checkbox('Prix', key='price', enable_events=True, background_color='black', text_color='white', font=('Helvetica', 18)),
         sg.Checkbox('Type de restaurant', key='cuisine', enable_events=True, background_color='black', text_color='white', font=('Helvetica', 18))],
        [sg.Checkbox('Note', key='rating', enable_events=True, background_color='black', text_color='white', font=('Helvetica', 18)),
         sg.Checkbox('Temps d’attente maximum', key='wait_time', enable_events=True, background_color='black', text_color='white', font=('Helvetica', 18))],
        [sg.Button('Rechercher', font=('Helvetica', 14)), sg.Button('Quitter', font=('Helvetica', 14))]
    ]

    window = sg.Window('Sélection de Restaurant', layout, finalize=True, element_justification='center', background_color='black', resizable=True, size=(800, 600))
    window.Maximize()

    def enforce_two_criteria():
        selected_criteria = [values['price'], values['cuisine'], values['rating'], values['wait_time']]
        if sum(selected_criteria) > 2:
            for key in ['price', 'cuisine', 'rating', 'wait_time']:
                if values[key] and event != key:
                    window[key].update(value=False)

    while True:
        event, values = window.read()

        if event == sg.WINDOW_CLOSED or event == 'Quitter':
            break

        if event in ['price', 'cuisine', 'rating', 'wait_time']:
            enforce_two_criteria()

        if event == 'Rechercher':
            selected_criteria = [key for key in ['price', 'cuisine', 'rating', 'wait_time'] if values[key]]

            if len(selected_criteria) != 2:
                sg.Popup("Veuillez sélectionner exactement deux critères.", text_color='white', background_color='black')
                continue

            input_layout = []
            if 'price' in selected_criteria:
                input_layout.append([sg.Text("Prix maximum :", text_color='white', background_color='black'), sg.Input(key='price_value')])
            if 'cuisine' in selected_criteria:
                input_layout.append([sg.Text("Type de restaurant :", text_color='white', background_color='black'), sg.Combo(cuisine_options, key='cuisine_value')])
            if 'rating' in selected_criteria:
                input_layout.append([sg.Text("Note minimale de satisfaction :", text_color='white', background_color='black'), sg.Input(key='rating_value')])
            if 'wait_time' in selected_criteria:
                input_layout.append([sg.Text("Temps d’attente maximum (service) :", text_color='white', background_color='black'), sg.Input(key='wait_time_value')])

            input_layout.append([sg.Button('Confirmer'), sg.Button('Annuler')])

            input_window = sg.Window('Entrée des Critères', input_layout, finalize=True, element_justification='center', background_color='black')

            while True:
                input_event, input_values = input_window.read()

                if input_event == sg.WINDOW_CLOSED or input_event == 'Annuler':
                    break

                if input_event == 'Confirmer':
                    criteria = {}
                    if 'price' in selected_criteria:
                        try:
                            criteria['price'] = float(input_values['price_value'])
                        except ValueError:
                            sg.Popup("Valeur de prix invalide.", text_color='white', background_color='black')
                            continue

                    if 'cuisine' in selected_criteria:
                        try:
                            criteria['cuisine'] = int(input_values['cuisine_value'].split(":")[0])
                        except (ValueError, IndexError):
                            sg.Popup("Valeur de type de restaurant invalide.", text_color='white', background_color='black')
                            continue

                    if 'rating' in selected_criteria:
                        try:
                            criteria['rating'] = int(input_values['rating_value'])
                        except ValueError:
                            sg.Popup("Valeur de note invalide.", text_color='white', background_color='black')
                            continue

                    if 'wait_time' in selected_criteria:
                        try:
                            criteria['wait_time'] = int(input_values['wait_time_value'])
                        except ValueError:
                            sg.Popup("Valeur de temps d’attente invalide.", text_color='white', background_color='black')
                            continue

                    random_resto, message = get_closest_resto(criteria)

                    if random_resto:
                        resto_info = (
                            f"Nom: {random_resto[0]}\n"
                            f"Adresse: {random_resto[5]}, {random_resto[6]}, {random_resto[7]}\n"
                            f"Type de cuisine: {random_resto[2]}\n"
                            f"Prix: {random_resto[3]}\n"
                            f"Service: {random_resto[4]}\n"
                            f"Satisfaction: {random_resto[9]}"
                        )
                        sg.Popup(f"Restaurant sélectionné :\n\n{resto_info}", text_color='white', background_color='black')
                    else:
                        sg.Popup(message, text_color='white', background_color='black')

                    retry = sg.PopupYesNo("Voulez-vous essayer à nouveau avec d'autres critères ?", text_color='white', background_color='black')
                    if retry != 'Yes':
                        visited_restaurants.clear()
                        break

                    input_window.close()
                    break

            input_window.close()

    window.close()

if __name__ == "__main__":
    main()
