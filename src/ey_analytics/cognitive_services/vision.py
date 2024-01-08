import os
import logging
import azure.cognitiveservices.vision.computervision as computervisionsdk
import azure.ai.vision as visionsdk
from dotenv import load_dotenv

from ey_analytics.utils.logger import SetUpLogging
from ey_analytics.utils.keyvault import Keyvault


# Init logger
SetUpLogging().setup_logging()


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

    vision = Vision()
    remote_image_url = 'https://adlsestudos.blob.core.windows.net/images/snapshot.jpg'

    image_analysis = vision.image_analyzer(remote_image_url)
    vision.check_image_analysis(image_analysis)
    image_description = image_analysis.caption.content

    print(image_description)
