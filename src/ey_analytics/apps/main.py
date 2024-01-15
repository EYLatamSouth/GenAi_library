import cv2
import logging
from ey_analytics.utils.logger import SetUpLogging
from ey_analytics.openai_api import OpenAI
from ey_analytics.utils.storage import Storage
from ey_analytics.cognitive_services import Speech, Vision

# Init logger
SetUpLogging().setup_logging()

# Init OpenAI
openaiAPI = OpenAI()

# Init Speech
speech = Speech(recognition_language='pt-BR',
                synthesis_voice_name='pt-BR-GiovannaNeural')

# Init Vision
vision = Vision()

# Init Storage
storage = Storage()


def start_video():
    # Create a VideoCapture object
    video = cv2.VideoCapture(0)  # '0' represents the default camera, you can change it if you have multiple cameras

    # Check if the camera is opened successfully
    if not video.isOpened():
        logging.error("Failed to open the camera")
        exit()

    return video


def capture_frame(video, display: bool = False):
    # Capture frame-by-frame
    ret, frame = video.read()

    # If frame is read correctly, ret will be True
    if ret and display:
        # Display the resulting frame
        cv2.imshow("Camera", frame)
        return frame
    elif ret:
        return frame


def save_frame(frame, image_name: str = 'snapshot.jpg'):
    # Save the frame as an image file
    cv2.imwrite(image_name, frame)
    logging.info(f"Snapshot saved as {image_name}")


def frame_description(frame, container_name: str = 'images', image_name: str = 'snapshot.jpg'):
    save_frame(frame, image_name)
    remote_image_url = storage.upload_image(container_name=container_name, image_name=image_name)
    image_analysis = vision.image_analyzer(remote_image_url)
    vision.check_image_analysis(image_analysis)
    image_description = image_analysis.caption.content
    return image_description


def format_conditions(conditions: tuple,
                      format: str):

    if format == 'Texto':
        return conditions
    else:
        return [item.capitalize() + '.' for item in conditions]


def get_question(format: str):
    if format == 'Texto':
        return input('Digite sua pergunta: ')
    else:
        input("Pressione Enter para perguntar...")
        return speech.speech_to_text()


def respond(resposta: str,
            format: str):

    if format == 'Texto':
        logging.info(resposta)
    else:
        speech.text_to_speech(resposta)


def store_messages(pergunta: str,
                   resposta: str,
                   previous_messages: list,
                   previous_messages_limit: int):

    previous_messages.append({"role": "user", "content": pergunta})
    previous_messages.append({"role": "assistant", "content": resposta})

    # Limitar armazenamento de últimas mensagens
    if len(previous_messages) > 2 * previous_messages_limit:
        del previous_messages[:2]

    return previous_messages


def chatbot(perfil_sistema: str,
            format: str = 'Texto',
            previous_messages: list = [],
            previous_messages_limit: int = 3):

    exit_conditions = format_conditions(
        (":q", "quit", "exit", "sair", "pare", "parar"), format)
    restart_conditions = format_conditions(
        ("limpar", "clear", "restart", "reiniciar", "limpe", "reinicie"), format)

    video = start_video()

    texto = "Olá, eu me chamo Faustina. Como posso te ajudar hoje?"
    respond(texto, format)

    while True:

        # Pergunta
        pergunta = get_question(format)
        # pergunta = 'Imagine a cena a partir do que você vê'
        frame = capture_frame(video, display=False)

        # Validar da pergunta
        if len(pergunta) == 0:
            resposta = "Desculpe, não entendi sua pergunta. Poderia repetir?"
            respond(resposta, format)
            continue
        elif ('gerar' or 'imagem') in pergunta.lower():
            resposta = "Claro, me dê um instante"
            respond(resposta, format)
            openaiAPI.generate_image(pergunta)
            continue
        elif ('que você vê') in pergunta.lower():
            resposta = "Deixe me pensar por um momento"
            respond(resposta, format)
            image_description = frame_description(frame)
            pergunta = f'{pergunta} Elabore uma pequena descrição para: {image_description}'
        elif pergunta in exit_conditions:
            break
        elif pergunta in restart_conditions:
            previous_messages = []

        # Gerar Resposta
        resposta = openaiAPI.ChatCompletion(perfil_sistema,
                                            pergunta,
                                            previous_messages=previous_messages)

        if ('imagine a cena') in pergunta.lower():
            resposta = "Eu imagino a cena da seguinte maneira"
            respond(resposta, format)
            image_description = frame_description(frame)
            pergunta = f'{pergunta}: {resposta}'
            openaiAPI.generate_image(pergunta)

        # Tratar últimas mensagens
        previous_messages = store_messages(pergunta,
                                           resposta,
                                           previous_messages,
                                           previous_messages_limit)

        # Resposta
        respond(resposta, format)


def main():

    perfil_sistema = ("Você é uma agente de inovação senior do mercado de técnologia"
                      "chamada Faustina. Você tem amplo conhecimento sobre jogos,"
                      "trabalhando para a empresa Ernest Young ou EY. As respostas"
                      "devem ser formais e objetivas com no máximo 100 caracteres.")

    chatbot(perfil_sistema, format='fala')


if __name__ == "__main__":
    main()
