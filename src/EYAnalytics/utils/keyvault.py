import os
import logging
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

try:
    from EYAnalytics.utils.logger import SetUpLogging
except Exception:
    from logger import SetUpLogging

# Init logger
SetUpLogging().setup_logging()


@SetUpLogging.class_logger
class Keyvault():
    def __init__(self, keyvault_name: str = 'estudos-kv'):
        """
        Inicializa a classe Keyvault.

        Args:
            keyvault_name (str, opcional): O nome do Key Vault. Padrão é 'estudos-kv'.
        """

        self.azure_credential()
        self.config_keyvault(keyvault_name)

    def azure_credential(self):
        """
        Configura a credencial do Azure.

        Esta função utiliza o DefaultAzureCredential para obter as credenciais do Azure.
        """

        self.credential = DefaultAzureCredential()

    def config_keyvault(self, keyvault_name: str):
        """
        Configura o Key Vault.

        Args:
            keyvault_name (str): O nome do Key Vault.
        """
        self.secret_client = SecretClient(vault_url=f'https://{keyvault_name}.vault.azure.net/',
                                          credential=self.credential)

    def set_secret(self, secret_name: str, secret_value: str):
        """
        Define um segredo no Key Vault.

        Args:
            secret_name (str): O nome do segredo.
            secret_value (str): O valor do segredo.
        """

        secret = self.secret_client.set_secret(secret_name, secret_value)
        logging.info(f'Secret registrada com sucesso: {secret.name}')

    def get_secret(self, secret_name: str):
        """
        Define um segredo no Key Vault.

        Args:
            secret_name (str): O nome do segredo.
            secret_value (str): O valor do segredo.

        Returns:
            SecretProperties: As propriedades do segredo registrado.
        """

        secret = self.secret_client.get_secret(secret_name)
        logging.debug(f'Secret resgatada com sucesso: {secret.name}')
        return secret.value

    def get_secret_as_env(self, secret_name: str, env_secret_name: str = None):
        """
        Obtém um segredo do Key Vault e define como variável de ambiente.

        Args:
            secret_name (str): O nome do segredo.
            env_secret_name (str, opcional): O nome da variável de ambiente. Padrão é None.
                Se não for fornecido, o nome do segredo será usado como nome da variável de ambiente.
        """

        if env_secret_name is None:
            env_secret_name = secret_name

        if os.environ.get(env_secret_name) is None:
            os.environ[env_secret_name] = self.get_secret(
                secret_name=secret_name)
            logging.info(
                f'Secret registrada com sucesso como variável de ambiente: {env_secret_name}')
        else:
            logging.info(
                f'Secret registrada anteriormente como variável de ambiente. O valor de {env_secret_name} não será atualizado')


if __name__ == "__main__":
    kv = Keyvault()
    kv.get_secret_as_env('Teste', 'Teste')
    print(os.environ.get("Teste"))
