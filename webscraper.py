import requests
from bs4 import BeautifulSoup
from bs4 import Tag
import re

class Webscraper():
    def __init__(self) -> None:
        pass

    def execute(self) -> dict:
        namelink_dict = self.extract_namelink()
        detailed_dict = self.extract_details(namelink_dict)
        
        return detailed_dict
    
    # <p>
    #   <a data-cke-rtc-autolink="true" data-cke-rtc-autolink-text="https://apigateway.conectagov.estaleiro.serpro.gov.br/api-quitacao-eleitoral/v3/eleitores/quitacao-eleitoral" 
    #   data-cke-rtc-autolink-url="https://apigateway.conectagov.estaleiro.serpro.gov.br/api-quitacao-eleitoral/v3/eleitores/quitacao-eleitoral"
    #   href="https://apigateway.conectagov.estaleiro.serpro.gov.br/api-quitacao-eleitoral/v3/eleitores/quitacao-eleitoral"
    #   id="jazz_ui_ResourceLink_22">
    #       https://h-apigateway.conectagov.estaleiro.serpro.gov.br/api-quitacao-eleitoral/v3/eleitores/quitacao-eleitoral
    #   </a>
    # 
    #   </p>, <p><a data-cke-rtc-autolink="true" data-cke-rtc-autolink-text="https://apigateway.conectagov.estaleiro.serpro.gov.br/api-quitacao-eleitoral/v2/eleitores/certidao-quitacao-eleitoral" data-cke-rtc-autolink-url="https://apigateway.conectagov.estaleiro.serpro.gov.br/api-quitacao-eleitoral/v2/eleitores/certidao-quitacao-eleitoral" href="https://apigateway.conectagov.estaleiro.serpro.gov.br/api-quitacao-eleitoral/v2/eleitores/certidao-quitacao-eleitoral" id="jazz_ui_ResourceLink_23">https://h-apigateway.conectagov.estaleiro.serpro.gov.br/api-quitacao-eleitoral/v2/eleitores/certidao-quitacao-eleitoral</a></p>, <p><a class="external-link" href="https://h-apigateway.conectagov.estaleiro.serpro.gov.br/oauth2/jwt-token" target="_self" title="https://h-apigateway.conectagov.estaleiro.serpro.gov.br/oauth2/jwt-token">https://h-apigateway.conectagov.estaleiro.serpro.gov.br/oauth2/jwt-token</a></p>, <p> </p>, <p><strong>Para consultar a documentação técnica da API acesse:</strong></p>, <p><a class="external-link" href="https://www.gov.br/conecta/catalogo/apis/quitacao-eleitoral/Documentacao-API-Certidao-Quitacao-Eleitoral_v2.pdf/at_download/file" target="_self" title="https://www.gov.br/conecta/catalogo/apis/quitacao-eleitoral/Documentacao-API-Certidao-Quitacao-Eleitoral_v2.pdf/at_download/file">https://www.gov.br/conecta/catalogo/apis/quitacao-eleitoral/Documentacao-API-Certidao-Quitacao-Eleitoral_v2.pdf/at_download/file</a></p>, <p> </p>, <p><strong>Atenção:</strong> Caso seja a primeira integração desenvolvida para acesso a uma API da Plataforma Conecta, é necessário previamente cadastrar os <span id="docs-internal-guid-fa315e3d-7fff-dee9-10f8-411c6bec8ca9">IPs <span id="docs-internal-guid-fa315e3d-7fff-dee9-10f8-411c6bec8ca9">do órgão</span> para que se <span id="docs-internal-guid-fa315e3d-7fff-dee9-10f8-411c6bec8ca9"></span>proceda a criação de regra de firewall no Serpro que permita o acesso <span id="docs-internal-guid-fa315e3d-7fff-dee9-10f8-411c6bec8ca9">à Plataforma</span>.​</span></p>, <p> </p>, <p><span><strong>Atenção:</strong> Para geração das chaves de acesso, consulte a seção de Gestor Consumidor de APIs do Gerenciador Conecta em:</span></p>, <ul>
    # <li><span><a class="external-link" href="https://gerenciador-conecta.readthedocs.io/manual_recebedor_dados.html#roteiro-geracao-chaves-acesso" target="_blank" title="https://gerenciador-conecta.readthedocs.io/manual_recebedor_dados.html#roteiro-geracao-chaves-acesso">https://doc.conectagov.estaleiro.serpro.gov.br/man/gestorConsumidorAPIs/#geracao-das-chaves-de-acesso</a></span></li>
    # </ul>

    def search_for_link(self, tag: Tag, link):
        # list(map(lambda elem: elem ,tag.find_next_siblings()))
        next_siblings = tag.find_next_siblings()

        return next_siblings

    def extract_details(self, namelink_dict: dict) -> dict:
        detailed_dict_list = []
        apis_without_detalhamento_tecnico = 0

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
            
            if (len(endpoint_classes) > 0):
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

            endpoints = list(filter(lambda elem: elem != None and elem != [], endpoints))

            detailed_dict_item["endpoints"] = endpoints

            if len(endpoints) == 0:
                apis_without_detalhamento_tecnico += 1

            detailed_dict_list.append(detailed_dict_item)

        print(apis_without_detalhamento_tecnico)

        return


    def extract_namelink(self) -> dict:
        main_page_content = requests.get("https://www.gov.br/conecta/catalogo/").content
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