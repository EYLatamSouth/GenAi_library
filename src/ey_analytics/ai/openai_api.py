import os
import time
import json
import openai
import logging
import requests
from PIL import Image
from io import BytesIO
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv


from ey_analytics.utils.logger import SetUpLogging
from ey_analytics.utils.keyvault import Keyvault


# Init logger
SetUpLogging().setup_logging()


@SetUpLogging.class_logger
class OpenAI():
    def __init__(self,
                 env_path: str = None,
                 api_type: str = 'azure',
                 api_version: str = '2023-03-15-preview'):
        """
        Inicializa a classe OpenAI.

        Args:
            env_path (str, opcional): O caminho para o arquivo de configuração do ambiente. Padrão é None.
            api_type (str, opcional): O tipo de API para o OpenAI. Padrão é 'azure'.
            api_version (str, opcional): A versão da API do OpenAI. Padrão é '2023-03-15-preview'.
        """

        os.environ["OPENAI_API_TYPE"] = api_type
        os.environ["OPENAI_API_VERSION"] = api_version

        # Init keyvault
        self.kv = Keyvault()
        self.load_env(env_path)
        self.config_openai()

    def azure_credential(self):
        """
        Configura a credencial do Azure.

        Esta função utiliza o DefaultAzureCredential para obter as credenciais do Azure.
        """

        self.credential = DefaultAzureCredential()

    def openai_token(self):
        """
        Obtém o token do OpenAI.

        Esta função utiliza a credencial para obter o token de autenticação do OpenAI
        para a URL "https://cognitiveservices.azure.com/.default".
        """

        self.openai_token = self.credential.get_token(
            "https://cognitiveservices.azure.com/.default")
        self.token = self.openai_token.token

    def refresh_openai_token(self):
        """
        Atualiza o token do OpenAI, se necessário.

        Se o token do OpenAI estiver prestes a expirar (com uma margem de 60 segundos),
        o token será atualizado definindo a variável de ambiente "OPENAI_API_KEY".
        """

        if self.openai_token.expires_on < int(time.time()) - 60:
            os.environ["OPENAI_API_KEY"] = self.token

    def load_env(self, env_path: str):
        """
        Carrega as variáveis de ambiente a partir de um arquivo ou do Key Vault.

        Args:
            env_path (str): O caminho para o arquivo de variáveis de ambiente. Se for None,
                as variáveis de ambiente serão obtidas do Key Vault.
        """

        if env_path is None:
            logging.info("Define API from Keyvault")
            self.kv.get_secret_as_env('AZURE-OPENAI-API-BASE', 'OPENAI_API_BASE')
            self.kv.get_secret_as_env('AZURE-OPENAI-API-KEY', 'OPENAI_API_KEY')
        else:
            logging.info("Define API from env")
            load_dotenv(dotenv_path=os.path.abspath(env_path))

    def config_openai(self):
        """
        Configura as variáveis de ambiente para a API do OpenAI.

        Esta função define as variáveis necessárias para a configuração da API do OpenAI:
        - OPENAI_API_TYPE: Tipo da API do OpenAI.
        - OPENAI_API_BASE: URL base da API do OpenAI.
        - OPENAI_API_KEY: Chave de autenticação da API do OpenAI.
        - OPENAI_API_VERSION: Versão da API do OpenAI.
        """

        openai.api_type = os.environ.get("OPENAI_API_TYPE")
        openai.api_base = os.environ.get("OPENAI_API_BASE")
        openai.api_key = os.environ.get("OPENAI_API_KEY")
        openai.api_version = os.environ.get("OPENAI_API_VERSION")

    def Completion(self, prompt: str, deployment_name: str = 'text-davinci-003'):
        """
        Gera uma conclusão para um prompt fornecido usando o modelo de linguagem do OpenAI.

        Args:
            prompt (str): O texto de entrada ou prompt para gerar a conclusão.
            deployment_name (str, opcional): O nome da implantação do modelo. Padrão é 'text-davinci-003'.

        Returns:
            str: A conclusão gerada pelo modelo de linguagem.
        """

        logging.debug("Mensagem: " + prompt)

        response = openai.Completion.create(
            engine=deployment_name,
            prompt=prompt,
            temperature=1,
            max_tokens=500,
            top_p=0.5,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None)

        logging.debug("Complemento: " + json.dumps(response))

        resposta = response['choices'][0]['text']

        return resposta

    def ChatCompletion(self, perfil_sistema: str, message: str,
                       deployment_name: str = 'gpt-35-turbo-16k', previous_messages=[]):
        """
        Gera uma resposta em um chatbot usando o modelo de linguagem do OpenAI.

        Args:
            perfil_sistema (str): O perfil do sistema ou ação inicial.
            message (str): A mensagem do usuário para obter a resposta.
            deployment_name (str, opcional): O nome da implantação do modelo. Padrão é 'gpt-35-turbo'.
            previous_messages (list, opcional): Mensagens anteriores na conversa. Padrão é [].

        Returns:
            str: A resposta gerada pelo chatbot.
        """

        system_profile = {"role": "system", "content": perfil_sistema}
        user_message = {"role": "user", "content": message}

        messages = []
        messages.append(system_profile)
        messages.extend(previous_messages)
        messages.append(user_message)

        str_messages = ','.join(json.dumps(item) for item in messages)
        logging.debug("Mensagem: " + str_messages)

        response = openai.ChatCompletion.create(
            engine=deployment_name,
            messages=messages,
            temperature=0.7,
            max_tokens=800,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None)
        logging.debug("Resposta: " + json.dumps(response))

        return response['choices'][0]['message']['content']

    def generate_image(self, message: str, image_name: str = 'gen_image.jpg'):
        """
        Gera uma imagem com base em um texto usando o modelo DALL·E do OpenAI.

        Args:
            message (str): O texto para gerar a imagem.
            image_name (str, opcional): O nome do arquivo de imagem. Padrão é 'image.jpg'.

        Returns:
            str: A URL da imagem gerada.
        """

        url = "{}dalle/text-to-image?api-version={}".format(os.environ.get("OPENAI_API_BASE"), '2023-09-15-preview')
        headers = {"api-key": os.environ.get("OPENAI_API_KEY"), "Content-Type": "application/json"}
        body = {
            "caption": message,
            "resolution": "1024x1024"
        }
        submission = requests.post(url, headers=headers, json=body)
        operation_location = submission.headers['Operation-Location']
        retry_after = submission.headers['Retry-after']
        status = ""
        while (status != "Succeeded"):
            time.sleep(int(retry_after))
            response = requests.get(operation_location, headers=headers)
            status = response.json()['status']
        image_url = response.json()['result']['contentUrl']

        # Salvar imagem
        img_data = requests.get(image_url).content
        with open(image_name, 'wb') as handler:
            handler.write(img_data)

        # Mostrar imagem
        Image.open(BytesIO(img_data)).show()

        return image_url


if __name__ == "__main__":
    openaiAPI = OpenAI()
    system = "Se comporte como um assistente empresarial."
    message = "Escreva um e-mail para a equipe de marketing direcionando os investimentos"
    resposta = openaiAPI.ChatCompletion(system,message)
    print(resposta)

    # message = "a home built in a huge Soap bubble, windows, doors, porches, awnings, middle of SPACE, cyberpunk lights, Hyper Detail, 8K, HD, Octane Rendering, Unreal Engine, V-Ray, full hd -- s5000 --uplight --q 3 --stop 80--w 0.5 --ar 1:3"
    # image = openaiAPI.generate_image(message)
    # print(image)
