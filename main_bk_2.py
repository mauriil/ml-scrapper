import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

class Scraper():

    def scraping(self):
        # User search
        product_name = input("\nProducto: ")
        # Clean the user input
        cleaned_name = product_name.replace(" ", "-").lower()
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
                # get the price
                price = post.find('span', class_='andes-money-amount__fraction').text
                # get the url post
                post_link = post.find("a")["href"]
                # get the url image
                try:
                    img_link = post.find("img")["data-src"]
                except:
                    img_link = post.find("img")["src"]

                product_detail = requests.get(post_link)
                product_soup = BeautifulSoup(product_detail.text, 'html.parser')

                # Encontrar todos los elementos de la tabla de especificaciones
                especificaciones = product_soup.find_all('tr', class_='andes-table__row')

                # Inicializar un diccionario para almacenar las especificaciones
                especificaciones_dict = {}
                especificaciones_dict["Precio"] = price

                # Iterar sobre las especificaciones y almacenarlas en el diccionario
                for especificacion in especificaciones:
                    th = especificacion.find('th', class_='andes-table__header')
                    td = especificacion.find('td', class_='andes-table__column')

                    if th and td:
                        especificaciones_dict[th.text.strip()] = td.text.strip()

                # Mostrar el diccionario de especificaciones
                print("Especificaciones:")
                for key, value in especificaciones_dict.items():
                    print(f"{key}: {value}")

                # quisiera que me ayudes a mejorar este codidgo, teniendo en cuenta de que tenemos unas especificaciones con sus valores,
                # me gustaria que se pueda comparar por cada producto encontrado el valor de cada especificacion junto a su precio,
                # siendo que la comparacion ganadora es siempre la que tenga mayor valor (enn promedio) y menor precio.
                # hay que tener en cuenta que si tenemos dos productos con las mismas especificaciones,
                # el producto con el menor precio es el ganador.
                # ademas, hay productos que no tienen especificaciones, por lo que hay que tener en cuenta que no se puede comparar.
                # por ejemplo, si tenemos dos productos con las siguientes especificaciones y precios:
                # producto 1:
                # - especificacion 1: 10
                # - especificacion 2: 20
                # - especificacion 3: 30
                # - Precio: $100
                # producto 2:
                # - especificacion 1: 20
                # - especificacion 2: 10\
                # - especificacion 3: 40
                # - Precio: $50
                # producto 1: $100
                # producto 2: $50
                # el producto ganador es el producto 1 con el precio $100 porque el valor promedio de las especificaciones es $20 y el precio es $100.





                # show the data already scraped
                # print(f"{c}. {title}, {price}, {post_link}, {img_link}")

                # save in a dictionary
                post_data = {
                    "title": title,
                    "price": price,
                    "post link": post_link,
                    "image link": img_link
                }
                # save the dictionaries in a list
                self.data.append(post_data)
                c += 1

    def export_to_csv(self):
        # export to a csv file
        df = pd.DataFrame(self.data)
        df.to_csv(r"data/mercadolibre_scraped_data.csv", sep=";")

if __name__ == "__main__":
    s = Scraper()
    s.scraping()
    s.export_to_csv()
