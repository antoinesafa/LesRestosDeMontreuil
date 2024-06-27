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

        cursor.execute("SELECT libelle_cuisine, type_cuisine FROM cuisine ORDER BY type_cuisine")
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


def get_restos():
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
        cursor.execute("SELECT nom, id_restau FROM resto WHERE actif = 't'")
        restos = cursor.fetchall()
        return restos
    except psycopg2.Error as e:
        print(f"Erreur lors de la connexion à PostgreSQL: {e}")
        return []
    finally:
        if conn:
            cursor.close()
            conn.close()


def insert_visite(visite_data):
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
        cursor.execute("""
            INSERT INTO visite (dt_visite, id_restau, prix, satisfaction, service)
            VALUES (%s, %s, %s, %s, %s)
        """, visite_data)
        conn.commit()
        return True
    except psycopg2.Error as e:
        print(f"Erreur lors de l'insertion dans PostgreSQL: {e}")
        return False
    finally:
        if conn:
            cursor.close()
            conn.close()


def insert_or_update_resto(resto_data, is_update=False, resto_id=None):
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

        if is_update:
            query = """
                UPDATE resto
                SET nom = %s, actif = %s, type_cuisine = %s, prix = %s, service = %s,
                    adresse_rue = %s, adresse_cp = %s, adresse_ville = %s,
                    places = %s, satisfaction = %s
                WHERE id_restau = %s
            """
            cursor.execute(query, resto_data + (resto_id,))
        else:
            query = """
                INSERT INTO resto (nom, actif, type_cuisine, prix, service,
                    adresse_rue, adresse_cp, adresse_ville, places, satisfaction)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, resto_data)

        conn.commit()
        return True
    except psycopg2.Error as e:
        print(f"Erreur lors de l'insertion ou de la mise à jour dans PostgreSQL: {e}")
        return False
    finally:
        if conn:
            cursor.close()
            conn.close()


def main():
    global visited_restaurants

    cuisines = get_cuisines()
    cuisine_options = [f"{cuisine[0]}: {cuisine[1]}" for cuisine in cuisines]

    layout = [
        [sg.Text("Veuillez choisir deux critères parmi les suivants :", text_color='white', background_color='black',
                 font=('Helvetica', 14))],
        [sg.Text(" ", size=(1, 2), background_color='black')],
        [sg.Checkbox('Prix', key='price', enable_events=True, background_color='black', text_color='white',
                     font=('Helvetica', 18)),
         sg.Checkbox('Type de restaurant', key='cuisine', enable_events=True, background_color='black',
                     text_color='white', font=('Helvetica', 18))],
        [sg.Checkbox('Note', key='rating', enable_events=True, background_color='black', text_color='white',
                     font=('Helvetica', 18)),
         sg.Checkbox('Temps d’attente maximum', key='wait_time', enable_events=True, background_color='black',
                     text_color='white', font=('Helvetica', 18))],
        [sg.Button('Valider', size=(10, 1), font=('Helvetica', 14)),
         sg.Button('Ajouter une Visite', size=(15, 1), font=('Helvetica', 14)),
         sg.Button('Gérer les Restaurants', size=(20, 1), font=('Helvetica', 14))],
    ]

    window = sg.Window('Sélection de Restaurant', layout, finalize=True, element_justification='center',
                       background_color='black')

    while True:
        event, values = window.read()

        if event == sg.WINDOW_CLOSED:
            break

        if event == 'Valider':
            selected_criteria = [key for key in ['price', 'cuisine', 'rating', 'wait_time'] if values[key]]
            if len(selected_criteria) != 2:
                sg.Popup("Veuillez choisir exactement deux critères.", text_color='white', background_color='black')
                continue

            input_layout = []

            if 'price' in selected_criteria:
                input_layout.append([sg.Text("Prix maximum :", text_color='white', background_color='black'),
                                     sg.Input(key='price_value')])
            if 'cuisine' in selected_criteria:
                input_layout.append([sg.Text("Type de restaurant :", text_color='white', background_color='black'),
                                     sg.Combo(cuisine_options, key='cuisine_value')])
            if 'rating' in selected_criteria:
                input_layout.append(
                    [sg.Text("Note minimale de satisfaction :", text_color='white', background_color='black'),
                     sg.Input(key='rating_value')])
            if 'wait_time' in selected_criteria:
                input_layout.append(
                    [sg.Text("Temps d’attente maximum (service) :", text_color='white', background_color='black'),
                     sg.Input(key='wait_time_value')])

            input_layout.append([sg.Button('Confirmer'), sg.Button('Annuler')])

            input_window = sg.Window('Entrée des Critères', input_layout, finalize=True, element_justification='center',
                                     background_color='black')

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
                            criteria['cuisine'] = int(input_values['cuisine_value'].split(":")[1])
                        except (ValueError, IndexError):
                            sg.Popup("Valeur de type de restaurant invalide.", text_color='white',
                                     background_color='black')
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
                            sg.Popup("Valeur de temps d’attente invalide.", text_color='white',
                                     background_color='black')
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
                        sg.Popup(f"Restaurant sélectionné :\n\n{resto_info}", text_color='white',
                                 background_color='black')
                    else:
                        sg.Popup(message, text_color='white', background_color='black')

                    retry = sg.PopupYesNo("Voulez-vous essayer à nouveau avec d'autres critères ?", text_color='white',
                                          background_color='black')
                    if retry != 'Yes':
                        visited_restaurants.clear()
                        break

                    input_window.close()
                    break

            input_window.close()

        if event == 'Ajouter une Visite':
            restos = get_restos()
            resto_options = [f"{resto[0]}" for resto in restos]
            resto_dict = {resto[0]: resto[1] for resto in restos}

            visite_layout = [
                [sg.Text("Nom du restaurant :", text_color='white', background_color='black'),
                 sg.Combo(resto_options, key='resto_nom')],
                [sg.Text("Comment était le prix :", text_color='white', background_color='black'),
                 sg.Combo(["mauvais", "moyen", "bien"], key='prix')],
                [sg.Text("Comment était le service :", text_color='white', background_color='black'),
                 sg.Combo(["mauvais", "moyen", "bien"], key='service')],
                [sg.Text("Quelle appréciation globale :", text_color='white', background_color='black'),
                 sg.Combo(["mauvais", "moyen", "bien"], key='satisfaction')],
                [sg.Button('Enregistrer'), sg.Button('Annuler')]
            ]

            visite_window = sg.Window('Ajouter une Visite', visite_layout, finalize=True,
                                      element_justification='center', background_color='black')

            while True:
                visite_event, visite_values = visite_window.read()

                if visite_event == sg.WINDOW_CLOSED or visite_event == 'Annuler':
                    break

                if visite_event == 'Enregistrer':
                    try:
                        resto_nom = visite_values['resto_nom']
                        resto_id = resto_dict[resto_nom]
                        prix = {"mauvais": 1, "moyen": 2, "bien": 3}[visite_values['prix']]
                        service = {"mauvais": 1, "moyen": 2, "bien": 3}[visite_values['service']]
                        satisfaction = {"mauvais": 1, "moyen": 2, "bien": 3}[visite_values['satisfaction']]
                        dt_visite = date.today()
                        visite_data = (dt_visite, resto_id, prix, satisfaction, service)

                        if insert_visite(visite_data):
                            sg.Popup("Visite ajoutée avec succès.", text_color='white', background_color='black')
                        else:
                            sg.Popup("Erreur lors de l'ajout de la visite.", text_color='white',
                                     background_color='black')
                    except Exception as e:
                        sg.Popup(f"Erreur lors de l'ajout de la visite: {e}", text_color='white',
                                 background_color='black')
                    break

            visite_window.close()

        if event == 'Gérer les Restaurants':
            cuisine_options = [cuisine[0] for cuisine in cuisines]
            resto_data = {
                'nom': '',
                'actif': 'oui',
                'type_cuisine': 1,
                'prix': 1,
                'service': 1,
                'adresse_rue': '',
                'adresse_cp': '',
                'adresse_ville': '',
                'places': '',
                'satisfaction': 1,
            }

            def resto_form_layout(is_update=False, resto=None):
                if is_update and resto:
                    resto_data.update({
                        'nom': resto[0],
                        'actif': 'oui' if resto[1] else 'non',
                        'type_cuisine': resto[2],
                        'prix': resto[3],
                        'service': resto[4],
                        'adresse_rue': resto[5],
                        'adresse_cp': resto[6],
                        'adresse_ville': resto[7],
                        'places': resto[8],
                        'satisfaction': resto[9],
                    })

                return [
                    [sg.Text("Le nom:", text_color='white', background_color='black'),
                     sg.Input(default_text=resto_data['nom'], key='nom')],
                    [sg.Text("Ouvert:", text_color='white', background_color='black'),
                     sg.Combo(['oui', 'non'], default_value=resto_data['actif'], key='actif')],
                    [sg.Text("Type de cuisine:", text_color='white', background_color='black'),
                     sg.Combo(cuisine_options, default_value=cuisine_options[resto_data['type_cuisine'] - 1],
                              key='type_cuisine')],
                    [sg.Text("A propos du prix:", text_color='white', background_color='black'),
                     sg.Slider(range=(1, 3), default_value=resto_data['prix'], orientation='h', key='prix')],
                    [sg.Text("A propos du service:", text_color='white', background_color='black'),
                     sg.Slider(range=(1, 3), default_value=resto_data['service'], orientation='h', key='service')],
                    [sg.Text("Adresse:", text_color='white', background_color='black'),
                     sg.Input(default_text=resto_data['adresse_rue'], key='adresse_rue')],
                    [sg.Text("Code Postale:", text_color='white', background_color='black'),
                     sg.Input(default_text=resto_data['adresse_cp'], key='adresse_cp')],
                    [sg.Text("Ville:", text_color='white', background_color='black'),
                     sg.Input(default_text=resto_data['adresse_ville'], key='adresse_ville')],
                    [sg.Text("Nombre de places groupes max:", text_color='white', background_color='black'),
                     sg.Input(default_text=resto_data['places'], key='places')],
                    [sg.Text("Satisfaction globale:", text_color='white', background_color='black'),
                     sg.Slider(range=(1, 3), default_value=resto_data['satisfaction'], orientation='h',
                               key='satisfaction')],
                    [sg.Button('Enregistrer'), sg.Button('Annuler')]
                ]

            def add_or_edit_resto(is_update=False, resto=None):
                form_layout = resto_form_layout(is_update, resto)
                resto_window = sg.Window('Ajouter/Modifier Restaurant', form_layout, finalize=True,
                                         element_justification='center', background_color='black')

                while True:
                    form_event, form_values = resto_window.read()

                    if form_event == sg.WINDOW_CLOSED or form_event == 'Annuler':
                        break

                    if form_event == 'Enregistrer':
                        try:
                            nom = form_values['nom']
                            actif = form_values['actif'] == 'oui'
                            type_cuisine = next(
                                (cuisine[1] for cuisine in cuisines if cuisine[0] == form_values['type_cuisine']), 1)
                            prix = int(form_values['prix'])
                            service = int(form_values['service'])
                            adresse_rue = form_values['adresse_rue']
                            adresse_cp = form_values['adresse_cp']
                            adresse_ville = form_values['adresse_ville']
                            places = form_values['places']
                            satisfaction = int(form_values['satisfaction'])

                            resto_data = (
                            nom, actif, type_cuisine, prix, service, adresse_rue, adresse_cp, adresse_ville, places,
                            satisfaction)

                            if insert_or_update_resto(resto_data, is_update, resto[-1] if resto else None):
                                sg.Popup("Restaurant ajouté/modifié avec succès.", text_color='white',
                                         background_color='black')
                            else:
                                sg.Popup("Erreur lors de l'ajout/modification du restaurant.", text_color='white',
                                         background_color='black')
                        except Exception as e:
                            sg.Popup(f"Erreur: {e}", text_color='white', background_color='black')
                        break

                resto_window.close()

            add_or_edit_resto()

    window.close()


if __name__ == "__main__":
    main()
