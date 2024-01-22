import cv2
import logging
from ey_analytics.utils.logger import SetUpLogging
from ey_analytics.utils.storage import Storage
from ey_analytics.cognitive_services.cognitive_services import Speech, Vision

# Init logger
SetUpLogging().setup_logging()

# Init Cognitives
speech = Speech(synthesis_voice_name="en-US-JennyMultilingualNeural")
vision = Vision()
storage = Storage()

# Create a VideoCapture object
cap = cv2.VideoCapture(
    0
)  # '0' represents the default camera, you can change it if you have multiple cameras

# Check if the camera is opened successfully
if not cap.isOpened():
    logging.error("Failed to open the camera")
    exit()

# Read and display frames from the camera
while True:
    # Capture frame-by-frame
    ret, frame = cap.read()

    # If frame is read correctly, ret will be True
    if ret:
        # Display the resulting frame
        cv2.imshow("Camera", frame)

        # Press 's' to capture a snapshot
        if cv2.waitKey(1) == ord("s"):
            container_name = "images"
            image_name = "snapshot.jpg"

            # Save the frame as an image file
            cv2.imwrite(image_name, frame)
            logging.info("Snapshot saved as snapshot.jpg")

            remote_image_url = storage.upload_image(
                container_name=container_name, image_name=image_name
            )

            image_analysis = vision.image_analyzer(remote_image_url)
            vision.check_image_analysis(image_analysis)
            image_description = image_analysis.caption.content

            speech.text_to_speech(text=image_description)

            break

    # Exit the loop if 'q' is pressed
    if cv2.waitKey(1) == ord("q"):
        break

# Release the VideoCapture object and close all windows
cap.release()
cv2.destroyAllWindows()
