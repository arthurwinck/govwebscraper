import requests
import re
import json
from bs4 import BeautifulSoup, Tag
from datetime import datetime

CONECTA_CATALOGO_API_URL = "https://www.gov.br/conecta/catalogo/"
EXPORT_FILE_PATH = "./json/"

class Webscraper():
    def __init__(self) -> None:
        pass

    def execute(self) -> None:
        namelink_dict = self.extract_namelink()
        detailed_dict = self.extract_details(namelink_dict)
        self.export_to_json(detailed_dict)

    def export_to_json(self, dict: dict):
        json_str = json.dumps(dict, indent=4, ensure_ascii=False)

        file_path = f"{EXPORT_FILE_PATH}/govapi-{datetime.today().strftime('%Y%m%d%H%M%S')}.json"
        with open(file_path, 'w', encoding='utf8') as file:
            file.write(json_str)

    def extract_meta_infos(self, site: BeautifulSoup, meta_info_list: list, dict: dict):
        for meta_info in meta_info_list:
            if site.find(id=meta_info) is not None:
                meta_info_text = site.find(id=meta_info).find_all('p')[1].text
                if meta_info == "tags":
                    dict[meta_info] = list(filter(lambda elem: elem != "", meta_info_text.split("#")))
                else:
                    dict[meta_info] = meta_info_text
            else:
                dict[meta_info] = None

    def extract_list(self, value):
        if isinstance(value, list):
            return value.pop()
        return value

    def search_for_link(self, tag: Tag, link):
        next_siblings = tag.find_next_siblings()

        link_list = []

        for sibling in next_siblings:
            all_links_in_sibling = sibling.find_all('a')

            for link in all_links_in_sibling:
                link_list.append(link.get('href'))

        return link_list

    def extract_details(self, namelink_dict: dict) -> dict:
        detailed_dict_list = []
        apis_without_detalhamento_tecnico = 0
        
        print(f"Quantidade de APIs mapeadas: {len(namelink_dict)}")

        for api_name, link in namelink_dict.items():
            detailed_dict_item = {}
            
            detailed_dict_item["nome"] = api_name
            detailed_dict_item["link"] = link

            detailed_page_content = requests.get(link).content
            site = BeautifulSoup(detailed_page_content, 'html.parser')

            desc = ""
            for descs in site.find(id="descricao").find_all("p"):
                desc += f"{descs.text}\n"

            detailed_dict_item["descricao"] = desc

            endpoints = []

            # Não busca todos os endpoints, é necessário uma estratégia para buscar os endpoints certinho
            endpoint_classes = site.find_all(class_="api-endpoint-producao")
            endpoints_by_class = []
            
            for endpoint in endpoint_classes:
                endpoints_by_class.append(endpoint.text.strip())

            # Necessário o slicing pois detalhamento-tecnico é usado em duas seções (o header do accordion e o body dele, por isso só pegamos o segundo div) 
            endpoint_tags_regex = site.find_all(class_="detalhamento-tecnico")[1::2]
            endpoints_by_regex = []

            if (len(endpoint_tags_regex) != 0):
                endpoints_by_regex = []

                [endpoint_tag] = endpoint_tags_regex
                endpoints_by_regex.extend(list(map(lambda element: self.search_for_link(element, link), endpoint_tag.find_all(["p", "span", "b"], string=re.compile("Endpoint")))))

            endpoints.extend(endpoints_by_class)
            endpoints.extend(endpoints_by_regex)

            endpoints = list(map(lambda filtered_elem: self.extract_list(filtered_elem), filter(lambda elem: elem != None and elem != [] and elem != "", endpoints)))

            detailed_dict_item["endpoints"] = endpoints

            if len(endpoints) == 0:
                apis_without_detalhamento_tecnico += 1

            meta_info_list = ["tecnologias", "tags", "seguranca", "hospedagem"]
            self.extract_meta_infos(site, meta_info_list, detailed_dict_item)
            
            detailed_dict_list.append(detailed_dict_item)

        return detailed_dict_list


    def extract_namelink(self) -> dict:
        main_page_content = requests.get(CONECTA_CATALOGO_API_URL).content
        site = BeautifulSoup(main_page_content, "html.parser")
        apis_section = site.find(class_="apis")
        rows = apis_section.find_all(class_="row")

        api_card_dict = {}
        for row in rows:
            api_cards_item = row.find_all("a")
            if len(api_cards_item) != 0:
                for api_card in api_cards_item:
                    if api_card is not None:
                        api_card_dict[api_card.find("p").text] = api_card.get("href")

        return api_card_dict