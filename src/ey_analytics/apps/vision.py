import os
import logging
from ey_analytics.utils.logger import SetUpLogging
from ey_analytics.utils.keyvault import Keyvault


# Init logger
SetUpLogging().setup_logging()

# Init keyvault
kv = Keyvault()


def load_env(env_path: str = None):
    """
    Carrega as variáveis de ambiente necessárias para configurar a API de visão.

    Args:
        env_path (str, opcional): O caminho do arquivo de ambiente (dotenv).
        Se não for fornecido, as variáveis serão obtidas do Keyvault.
    """

    if env_path is None:
        logging.info("Define API from Keyvault")
        kv.get_secret_as_env("AZURE-COGNITIVE-KEY", "VISION_KEY")
        kv.get_secret_as_env("AZURE-COGNITIVE-ENDPOINT", "VISION_ENDPOINT")
    else:
        from dotenv import load_dotenv

        logging.info("Define API from env")
        load_dotenv(dotenv_path=os.path.abspath(env_path))


load_env()

urlA = "https://raw.githubusercontent.com/Azure-Samples/cognitive-services-sample-data-files/master/ComputerVision/Images/landmark.jpg"

urlB = "https://learn.microsoft.com/azure/cognitive-services/computer-vision/media/quickstarts/presentation.png"

coca_url = "https://adlsestudos.blob.core.windows.net/images/coca_snapshot.jpg"

snapshot_url = "https://adlsestudos.blob.core.windows.net/images/snapshot.jpg"

remote_image_url = snapshot_url

# Quickstart (v4.0 preview)

import azure.ai.vision as visionsdk

service_options = visionsdk.VisionServiceOptions(
    os.environ["VISION_ENDPOINT"], os.environ["VISION_KEY"]
)

vision_source = visionsdk.VisionSource(url=remote_image_url)

analysis_options = visionsdk.ImageAnalysisOptions()

analysis_options.features = (
    visionsdk.ImageAnalysisFeature.CAPTION | visionsdk.ImageAnalysisFeature.TEXT
)

analysis_options.language = "en"

analysis_options.gender_neutral_caption = True

image_analyzer = visionsdk.ImageAnalyzer(
    service_options, vision_source, analysis_options
)

result = image_analyzer.analyze()

if result.reason == visionsdk.ImageAnalysisResultReason.ANALYZED:
    if result.caption is not None:
        print(" Caption:")
        print(
            "   '{}', Confidence {:.4f}".format(
                result.caption.content, result.caption.confidence
            )
        )

    if result.text is not None:
        print(" Text:")
        for line in result.text.lines:
            points_string = (
                "{"
                + ", ".join([str(int(point)) for point in line.bounding_polygon])
                + "}"
            )
            print(
                "   Line: '{}', Bounding polygon {}".format(line.content, points_string)
            )
            for word in line.words:
                points_string = (
                    "{"
                    + ", ".join([str(int(point)) for point in word.bounding_polygon])
                    + "}"
                )
                print(
                    "     Word: '{}', Bounding polygon {}, Confidence {:.4f}".format(
                        word.content, points_string, word.confidence
                    )
                )

else:
    error_details = visionsdk.ImageAnalysisErrorDetails.from_result(result)
    print(" Analysis failed.")
    print("   Error reason: {}".format(error_details.reason))
    print("   Error code: {}".format(error_details.error_code))
    print("   Error message: {}".format(error_details.message))

##############################################################################################
# Quickstart (v3.2)

import time
import sys
from PIL import Image
from array import array
from msrest.authentication import CognitiveServicesCredentials

# from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
# from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes

import azure.cognitiveservices.vision.computervision as computervisionsdk

# https://learn.microsoft.com/en-us/python/api/overview/azure/cognitiveservices-vision-computervision-readme
"""
Authenticate
Authenticates your credentials and creates a client.
"""
subscription_key = os.environ["VISION_KEY"]
endpoint = os.environ["VISION_ENDPOINT"]

computervision_client = computervisionsdk.ComputerVisionClient(
    endpoint, CognitiveServicesCredentials(subscription_key)
)
"""
END - Authenticate
"""

"""
Quickstart variables
These variables are shared by several examples
"""
# Images used for the examples: Describe an image, Categorize an image, Tag an image,
# Detect faces, Detect adult or racy content, Detect the color scheme,
# Detect domain-specific content, Detect image types, Detect objects
images_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
"""
END - Quickstart variables
"""


"""
Tag an Image - remote
This example returns a tag (key word) for each thing in the image.
"""
print("===== Tag an image - remote =====")
# Call API with remote image
tags_result_remote = computervision_client.tag_image(remote_image_url)

# Print results with confidence score
print("Tags in the remote image: ")
if len(tags_result_remote.tags) == 0:
    print("No tags detected.")
else:
    for tag in tags_result_remote.tags:
        print("'{}' with confidence {:.2f}%".format(tag.name, tag.confidence * 100))
print()
"""
END - Tag an Image - remote
"""
print("End of Computer Vision quickstart.")
