import os
import logging
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

from ey_analytics.utils.logger import SetUpLogging
from ey_analytics.utils.keyvault import Keyvault


# Init logger
SetUpLogging().setup_logging()


@SetUpLogging.class_logger
class Speech():
    def __init__(self,
                 env_path: str = None,
                 recognition_language: str = 'pt-BR',
                 synthesis_voice_name: str = 'pt-BR-FranciscaNeural'):
        """
        Inicializa a classe.

        Args:
            env_path (str, opcional): O caminho para o arquivo de configuração do ambiente. Padrão: None.
            recognition_language (str, opcional): O idioma de reconhecimento de fala. Padrão: 'pt-BR'.
            synthesis_voice_name (str, opcional): O nome da voz de síntese. Padrão: 'pt-BR-FranciscaNeural'.
        """

        self.load_env(env_path)
        self.config_speech_API()
        self.config_speech_synthesizer(synthesis_voice_name)
        self.config_speech_recognizer(recognition_language)

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

            kv.get_secret_as_env('AZURE-COGNITIVE-KEY', 'AZURE_SPEECH_KEY')
            kv.get_secret_as_env('AZURE-COGNITIVE-REGION',
                                 'AZURE_SPEECH_REGION')
        else:
            logging.info("Define API from env")
            load_dotenv(dotenv_path=os.path.abspath(env_path))

    def config_speech_API(self):
        """
        Configura a API de fala usando as variáveis de ambiente definidas anteriormente.
        A API de fala é configurada com base nas variáveis de ambiente
        'AZURE_SPEECH_KEY' e 'AZURE_SPEECH_REGION'.

        Atributos:
            self.speech_config (speechsdk.SpeechConfig): Configuração da API de fala.
        """

        self.speech_config = speechsdk.SpeechConfig(
            subscription=os.environ.get('AZURE_SPEECH_KEY'),
            region=os.environ.get('AZURE_SPEECH_REGION'))

    def config_speech_recognizer(self, recognition_language: str):
        """
        Configura o reconhecedor de fala com o idioma de reconhecimento especificado.
        https://learn.microsoft.com/en-us/azure/cognitive-services/speech-service/language-support?tabs=stt

        Args:
            recognition_language (str): O idioma para reconhecimento de fala.
        """

        self.speech_config.speech_recognition_language = recognition_language
        microphone_audio_config = speechsdk.audio.AudioConfig(
            use_default_microphone=True)
        self.speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config, audio_config=microphone_audio_config)

    def config_speech_synthesizer(self, synthesis_voice_name: str):
        """
        Configura o sintetizador de fala com o nome da voz de síntese especificada.
        https://learn.microsoft.com/en-us/azure/cognitive-services/speech-service/language-support?tabs=tts

        Args:
            synthesis_voice_name (str): O nome da voz de síntese.
        """

        self.speech_config.speech_synthesis_voice_name = synthesis_voice_name
        speaker_audio_config = speechsdk.audio.AudioOutputConfig(
            use_default_speaker=True)
        self.speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config, audio_config=speaker_audio_config)

    def speech_to_text(self):
        """
        Converte fala em texto.

        Returns:
            str: O texto reconhecido a partir da fala.
        """

        logging.info("Speak into your microphone.")
        speech_recognition_result = self.speech_recognizer.recognize_once_async().get()

        if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
            logging.info("Recognized: {}".format(
                speech_recognition_result.text))
        elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
            logging.info("No speech could be recognized: {}".format(
                speech_recognition_result.no_match_details))
        elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speech_recognition_result.cancellation_details
            logging.info("Speech Recognition canceled: {}".format(
                cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                logging.error("Error details: {}".format(
                    cancellation_details.error_details))
                logging.error(
                    "Did you set the speech resource key and region values?")

        return speech_recognition_result.text

    def text_to_speech(self, text: str):
        """
        Converte texto em fala.

        Args:
            text (str): O texto a ser convertido em fala.
        """

        speech_synthesizer_result = self.speech_synthesizer.speak_text_async(
            text).get()

        if speech_synthesizer_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            logging.info(
                "Speech synthesized to speaker for text [{}]".format(text))
        elif speech_synthesizer_result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speech_synthesizer_result.cancellation_details
            logging.info("Speech synthesis canceled: {}".format(
                cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                if cancellation_details.error_details:
                    logging.error("Error details: {}".format(
                        cancellation_details.error_details))
            logging.error("Did you update the subscription info?")
