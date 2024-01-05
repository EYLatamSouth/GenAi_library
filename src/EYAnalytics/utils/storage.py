import os
import logging
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient, ContentSettings

try:
    from EYAnalytics.utils.logger import SetUpLogging
    from EYAnalytics.utils.keyvault import Keyvault
except Exception:
    from logger import SetUpLogging
    from keyvault import Keyvault

# Init logger
SetUpLogging().setup_logging()


@SetUpLogging.class_logger
class Storage():
    def __init__(self, env_path: str = None):

        self.load_env(env_path)
        self.config_enpoint()
        self.config_blob_service_client()

    def load_env(self, env_path: str = None):
        """
        Carrega as variáveis de ambiente necessárias para configurar a API de fala.

        Args:
            env_path (str, opcional): O caminho do arquivo de ambiente (dotenv).
            Se não for fornecido, as variáveis serão obtidas do Keyvault.
        """

        if env_path is None:
            logging.info("Define API from Keyvault")

            # Init keyvault
            kv = Keyvault()

            kv.get_secret_as_env('AZURE-STORAGE-CONNECTION-STRING',
                                 'ADLS_CONNECTION_STRING')
            kv.get_secret_as_env('AZURE-STORAGE-KEY', 'ADLS_KEY')
            kv.get_secret_as_env(
                'AZURE-STORAGE-SERVICE-NAME', 'ADLS_SERVICE_NAME')

        else:
            logging.info("Define API from env")
            load_dotenv(dotenv_path=os.path.abspath(env_path))

    def config_enpoint(self):
        self.endpoint = f'https://{os.environ["ADLS_SERVICE_NAME"]}.blob.core.windows.net'

    def config_blob_service_client(self):
        self.blob_service_client = BlobServiceClient.from_connection_string(
            os.environ["ADLS_CONNECTION_STRING"])

    def upload_file(self, container_name: str, file_name: str, file_path = None, overwrite: bool = True):
        """
        Carrega um arquivo para o Azure Blob Storage.

        Esta função carrega o file_name especificado para o container_name especificado no Azure Blob Storage.
        Se o argumento overwrite não for fornecido, qualquer blob existente com o mesmo nome será sobrescrito.

        Args:
        container_name (str): O nome do contêiner no Azure Blob Storage onde o arquivo será carregado.
        file_name (str): O nome do arquivo (de preferência com seu caminho) que deve ser carregado.
        overwrite (bool, opcional): Uma bandeira indicando se deve sobrescrever o blob se ele já existir.
        O padrão é True.
        """
        blob_client = self.blob_service_client.get_blob_client(
            container=container_name, blob=file_name)

        if file_path is None:
            file_path = os.path.abspath(file_name)
        else:
            file_path = os.path.join(file_path, file_name)

        try:
            # Upload the snapshot to Azure Blob Storage
            with open(file_name, "rb") as file:
                blob_client.upload_blob(file, overwrite=overwrite)

            logging.info(f"File: {file_name} upload completed")
        except Exception as error_message:
            logging.error(
                f"Failed to upload {file_name}. Error: {str(error_message)}")
        finally:
            blob_client.close()

    def download_file(self, container_name: str, file_name: str, file_path=None):
        """
        Baixa um blob do Azure Blob Storage.

        Esta função baixa o blob especificado do container_name especificado no Azure Blob Storage e o salva no file_path especificado.

        Args:
        container_name (str): O nome do contêiner no Azure Blob Storage do qual o blob será baixado.
        file_name (str): O nome do blob que será baixado.
        file_path (str): O caminho onde o blob baixado deve ser salvo.

        Exemplo:
        download_blob("meuContainer", "meuArquivo", "/caminho/para/salvar/arquivo")
        """
        blob_client = self.blob_service_client.get_blob_client(
            container=container_name, blob=file_name)

        if file_path is None:
            file_path = os.path.abspath(file_name)
        else:
            file_path = os.path.join(file_path, file_name)

        try:
            with open(file_path, "wb") as download_file:
                download_data = blob_client.download_blob().readall()
                download_file.write(download_data)
            logging.info(f"File: {file_name}, download completed")
        except Exception as error_message:
            logging.error(
                f"Failed to download {file_name}. Error: {str(error_message)}")
        finally:
            blob_client.close()

    def download_all_files_in_container(self, container_name: str, local_directory_path: str):
        """
        Baixa todos os blobs em um contêiner Azure Blob Storage.

        Esta função baixa todos os blobs do container_name especificado no Azure Blob Storage e os salva na pasta especificada.

        Args:
        container_name (str): O nome do contêiner no Azure Blob Storage do qual os blobs serão baixados.
        local_directory_path (str): O caminho da pasta onde os blobs baixados devem ser salvos.

        Exemplo:
        download_all_files_in_container("meuContainer", "/caminho/para/salvar/arquivos")
        """
        container_client = self.blob_service_client.get_container_client(
            container_name)

        try:
            blob_list = container_client.list_blobs()
            for blob in blob_list:
                self.download_file(container_name, file_name=blob,
                                   file_path=local_directory_path)
        except Exception as error_message:
            logging.error(
                f"Failed to download {container_name}. Error: {str(error_message)}")
        finally:
            container_client.close()

    def upload_image(self, container_name: str, image_name: str, image_path=None, overwrite: bool = True):
        blob_client = self.blob_service_client.get_blob_client(
            container=container_name, blob=image_name)

        if image_path is None:
            image_path = os.path.abspath(image_name)
        else:
            image_path = os.path.join(image_path, image_name)

        try:
            # Upload the snapshot to Azure Blob Storage
            with open(image_name, "rb") as image_file:
                blob_client.upload_blob(image_file,
                                        overwrite=overwrite,
                                        content_settings=ContentSettings(content_type='image/jpeg'))
            logging.info("Image upload completed")

            remote_image_url = f'{self.endpoint}/{container_name}/{image_name}'
            return remote_image_url

        except Exception as error_message:
            logging.error(
                f"Failed to upload {image_name}. Error: {str(error_message)}")
        finally:
            blob_client.close()


if __name__ == "__main__":

    storage = Storage()
    storage.upload_image(container_name='images',
                         image_name='image.jpg', image_path='./media/')

    storage.download_file(container_name='images',
                          file_name='image.jpg')
