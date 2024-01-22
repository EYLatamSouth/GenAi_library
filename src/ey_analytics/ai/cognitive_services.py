import os
import logging
import azure.cognitiveservices.speech as speechsdk
import azure.cognitiveservices.vision.computervision as computervisionsdk
import azure.ai.vision as visionsdk
from dotenv import load_dotenv

try:
    from ey_analytics.utils.logger import SetUpLogging
    from ey_analytics.utils.keyvault import Keyvault
except Exception:
    from logger import SetUpLogging
    from keyvault import Keyvault

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


@SetUpLogging.class_logger
class Vision():
    def __init__(self,
                 env_path: str = None):

        self.load_env(env_path)
        self.config_vision_API()

    def load_env(self, env_path: str = None):
        """
        Carrega as variáveis de ambiente necessárias para configurar a API de visão.

        Args:
            env_path (str, opcional): O caminho do arquivo de ambiente (dotenv).
            Se não for fornecido, as variáveis serão obtidas do Keyvault.
        """

        if env_path is None:
            logging.info("Define API from Keyvault")

            # Init keyvault
            kv = Keyvault()

            kv.get_secret_as_env('AZURE-COGNITIVE-KEY', 'VISION_KEY')
            kv.get_secret_as_env('AZURE-COGNITIVE-REGION', 'VISION_REGION')
            kv.get_secret_as_env('AZURE-COGNITIVE-ENDPOINT', 'VISION_ENDPOINT')
        else:
            logging.info("Define API from env")
            load_dotenv(dotenv_path=os.path.abspath(env_path))

    def config_vision_API(self):
        self.service_options = visionsdk.VisionServiceOptions(os.environ["VISION_ENDPOINT"],
                                                              os.environ["VISION_KEY"])

    def config_analysis_options(self, language: str):
        # https://learn.microsoft.com/en-us/azure/cognitive-services/computer-vision/language-support
        self.analysis_options = visionsdk.ImageAnalysisOptions()
        self.analysis_options.language = language
        self.analysis_options.gender_neutral_caption = True

        self.analysis_options.features = (
            visionsdk.ImageAnalysisFeature.CAPTION |
            visionsdk.ImageAnalysisFeature.TEXT
        )

    def config_vision_source(self, remote_image_url: str):
        self.vision_source = visionsdk.VisionSource(url=remote_image_url)

    def image_analyzer(self, remote_image_url: str, language: str = 'en'):
        self.config_analysis_options(language)
        self.config_vision_source(remote_image_url)

        image_analyzer = visionsdk.ImageAnalyzer(self.service_options,
                                                 self.vision_source,
                                                 self.analysis_options)
        image_analysis = image_analyzer.analyze()
        return image_analysis

    def check_image_analysis(self, image_analysis):
        if image_analysis.reason == visionsdk.ImageAnalysisResultReason.ANALYZED:
            if image_analysis.caption is not None:
                self.caption_feature_results(image_analysis)
            elif image_analysis.text is not None:
                self.text_feature_results(image_analysis)
            else:
                logging.info("Image Analysis Feature not configured.")
        else:
            error_details = visionsdk.ImageAnalysisErrorDetails.from_result(
                image_analysis)
            logging.error("Analysis failed.")
            logging.error(" Error reason: {}".format(error_details.reason))
            logging.error(" Error code: {}".format(error_details.error_code))
            logging.error(" Error message: {}".format(error_details.message))

    def caption_feature_results(self, image_analysis):
        logging.info("Caption: " + "'{}', Confidence {:.4f}".format(
            image_analysis.caption.content, image_analysis.caption.confidence))

    def text_caption_feature_results(self, image_analysis):
        logging.info("Text:")
        for line in image_analysis.text.lines:
            points_list = [str(int(point)) for point in line.bounding_polygon]
            points_string = "{" + ", ".join(points_list) + "}"
            logging.info("Line: '{}', Bounding polygon {}".format(
                line.content, points_string))
            for word in line.words:
                points_list = [str(int(point))
                               for point in word.bounding_polygon]
                points_string = "{" + ", ".join(points_list) + "}"
                logging.info("Word: '{}', Bounding polygon {}, Confidence {:.4f}".format(word.content,
                                                                                         points_string,
                                                                                         word.confidence))


if __name__ == "__main__":
    speech = Speech()
    speech.text_to_speech(text='Olá Mundo!')

    vision = Vision()
    remote_image_url = 'https://adlsestudos.blob.core.windows.net/images/snapshot.jpg'

    image_analysis = vision.image_analyzer(remote_image_url)
    vision.check_image_analysis(image_analysis)
    image_description = image_analysis.caption.content

    speech.text_to_speech(text=image_description)
