import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_RIGHT

class Scraper():

    def scraping(self):
        # User search
        product_name = input("\nProducto: ")
        # Clean the user input
        cleaned_name = product_name.replace(" ", "-").lower()
         # Get excluded words
        excluded_words_input = input("Palabras excluidas (separadas por coma y/o espacio): ")
        if excluded_words_input:
            excluded_words = re.split(r',\s*|\s+', excluded_words_input)
        else:
            excluded_words = []
        # Create the urls to scrap
        urls = ['https://listado.mercadolibre.com.ar/' + cleaned_name]

        page_number = 50
        for i in range(0, 10000, 50):
            urls.append(f"{'https://listado.mercadolibre.com.ar/'}{cleaned_name}_Desde_{page_number + 1}_NoIndex_True")
            page_number += 50

        # create a list to save the data
        self.data = []
        # create counter
        c = 1

        # Iterate over each url
        for i, url in enumerate(urls, start=1):

            # Get the html of the page
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # take all posts
            content = soup.find_all('li', class_='ui-search-layout__item')

            # Check if there's no content to scrape
            if not content:
                print("\nTermino el scraping.")
                break

            print(f"\nScrapeando pagina numero {i}. {url}")

            # iteration to scrape posts
            for post in content:
                # get the title
                title = post.find('h2').text
                if any(word in title.lower() for word in excluded_words):
                    continue
                print(f"\n{c}. {title}")
                # get the price
                price = post.find('span', class_='andes-money-amount__fraction').text
                # get the url post
                post_link = post.find("a")["href"]
                # get the url image
                try:
                    img_link = post.find("img")["data-src"]
                except:
                    img_link = post.find("img")["src"]

                # Extract review score
                review_score = None
                review_info = post.find('span', class_='ui-pdp-review__rating')
                if review_info:
                    review_score = float(review_info.text)

                product_detail = requests.get(post_link)
                product_soup = BeautifulSoup(product_detail.text, 'html.parser')

                # get the price with discount
                price_tag = post.find('span', class_='andes-money-amount')
                has_discount = False
                if price_tag:
                    discounted_price = price_tag.text.strip()
                    price = float(re.sub(r'[,.]', '', price))
                    discounted_price = float(re.sub(r'[,.]', '', discounted_price[1:]))
                    if price > discounted_price:
                        has_discount = True
                else:
                    discounted_price = None

                # Encontrar todos los elementos de la tabla de especificaciones
                especificaciones = product_soup.find_all('tr', class_='andes-table__row')

                # Inicializar un diccionario para almacenar las especificaciones
                especificaciones_dict = {}

                # Iterar sobre las especificaciones y almacenarlas en el diccionario
                for especificacion in especificaciones:
                    th = especificacion.find('th', class_='andes-table__header')
                    td = especificacion.find('td', class_='andes-table__column')

                    if th and td:
                        especificaciones_dict[th.text.strip()] = td.text.strip()

                # Calcular el puntaje del producto
                score = self.calculate_score(especificaciones_dict, price, review_score, has_discount)

                # Mostrar el diccionario de especificaciones
                #print("Especificaciones:")
                #for key, value in especificaciones_dict.items():
                #    print(f"{key}: {value}")

                # Mostrar el puntaje del producto
                #print(f"Puntaje del producto: {score}")

                # save in a dictionary
                post_data = {
                    "title": title,
                    "price": price,
                    "discounted_price": discounted_price,
                    "has_discount": has_discount,
                    "post link": post_link,
                    "image link": img_link,
                    "review score": review_score,
                    "score": score
                }
                # save the dictionaries in a list
                self.data.append(post_data)
                c += 1

    def calculate_score(self, especificaciones_dict, price, review_score, has_discount):
        # Inicializar el puntaje total
        total_score = 0

        # Definir los criterios de puntuación para cada valor de especificación
        criterios_puntuacion = {
            # jabon y suavizantes
            "cantidad de lavados": {"umbral": 50},
            "fragancia": {"umbral": "Místico"},  # Ejemplo: Si la fragancia es "Místico", se considera perfecto
            # Autos y Motos
            "Año": {"umbral": 2010},  # Cuanto más reciente, mayor puntuación
            "Kilómetros": {"umbral": 50000},  # Menos kilometraje, mayor puntuación
            # Sillones y muebles
            "Material": {"umbral": "Cuero"},  # Calidad del material y durabilidad
            "Estilo": {"umbral": "Moderno"},  # Popularidad del estilo y diseño moderno
            # Hogar y productos de almacenamiento
            "Capacidad de almacenamiento": {"umbral": 100},  # Cuanto más grande, mayor puntuación
            # Electrodomésticos
            "Eficiencia energética": {"umbral": "Clase A"},  # Mayor eficiencia, mayor puntuación
            # Alimentos y supermercado
            "Fecha de vencimiento": {"umbral": "2023-12-31"},  # Productos frescos y con fecha de vencimiento lejana
            "unidades por pack": {"umbral": 4},
            # Productos de higiene y cuidado personal
            "Ingredientes": {"umbral": "Natural"},  # Productos naturales y de alta calidad
            # Ropa
            "Material": {"umbral": "Algodón"},  # Calidad del material
            # Electrónica
            "Eficiencia energética": {"umbral": "Clase A+"},  # Mayor eficiencia, mayor puntuación
            # Teléfonos celulares y smartphones
            "Calidad de la cámara": {"umbral": "12 MP"},  # Calidad de la cámara
            # Computadoras y notebooks
            "Memoria RAM": {"umbral": "8 GB"},  # Capacidad de la memoria RAM
        }

        # Calcular el puntaje basado en cada valor de especificación
        for especificacion, criterio in criterios_puntuacion.items():
            if especificacion in especificaciones_dict:
                valor_especificacion = especificaciones_dict[especificacion]

                # Comparar el valor de la especificación con el umbral y asignar puntos en consecuencia
                if isinstance(criterio["umbral"], int):
                    valor_numerico = int(re.findall(r'\d+', valor_especificacion)[0])
                    distancia = abs(valor_numerico - criterio["umbral"])
                    # Calcular el puntaje basado en la distancia al umbral
                    score = max(min(10 - distancia, 10), 1)
                    total_score += score
                else:
                    if valor_especificacion.lower() == criterio["umbral"].lower():
                        total_score += 10
                    else:
                        total_score += 1

        # Añadir puntaje basado en el precio (cuanto más bajo, más puntos)
        price_score = 100 / (1 + float(price))
        total_score += price_score

        # Añadir puntaje basado en la calificación de la revisión
        if review_score is not None:
            total_score += review_score

        # Añadir puntaje si el producto tiene descuento o tiene un precio con descuento
        if has_discount:
            # mientras más alto el precio con descuento, más puntos
            discount_score = 100 / (1 + float(price))
            total_score += discount_score

        return total_score

    def export_to_csv(self):
        # order the data by score in descending order
        self.data.sort(key=lambda x: x["score"], reverse=True)
        # ordenar por menor precio
        self.data.sort(key=lambda x: x["price"])
        # keep only the top 10
        self.data = self.data[:10]
        # export to a csv
        df = pd.DataFrame(self.data)
        df.to_csv(r"data/mercadolibre_scraped_data.csv", sep=";")

    def export_to_pdf(self):
        # Ordenar los datos por puntaje en orden descendente
        self.data.sort(key=lambda x: x["score"], reverse=True)
        # ordenar por menor precio
        self.data.sort(key=lambda x: x["price"])
        # Mantener solo los 10 mejores
        top_10_data = self.data[:10]

        # Crear un documento PDF
        pdf_filename = "data/top_10_products.pdf"
        doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
        styles = getSampleStyleSheet()

        # Crear una lista de elementos para el PDF
        pdf_elements = []

        # Agregar un título al PDF
        pdf_elements.append(Paragraph("Top 10 Productos", styles['Title']))

        # Iterar sobre los productos y agregar información al PDF
        for product in top_10_data:
            # Agregar imagen a la izquierda
            image = Image(product["image link"], width=100, height=100)
            pdf_elements.append(image)

            # Agregar datos a la derecha
            data_text = f"<b>{product['title']}</b><br/>" \
                        f"Precio: ${product['price']}<br/>" \
                        f"Precio con descuento: ${product['discounted_price']}<br/>" \
                        f"Tiene descuento: {product['has_discount']}<br/>" \
                        f"Puntaje: {product['score']}<br/>" \
                        f"Enlace: {product['post link']}"

            data_paragraph = Paragraph(data_text, styles['Normal'], bulletText='-')
            pdf_elements.append(data_paragraph)

            # Agregar espacio entre productos
            pdf_elements.append(Spacer(1, 12))

        # Agregar los elementos al documento PDF
        doc.build(pdf_elements)

        print(f"PDF generado: {pdf_filename}")


if __name__ == "__main__":
    s = Scraper()
    s.scraping()
    s.export_to_csv()
    s.export_to_pdf()
