import cv2
import logging
import tkinter as tk
from tkinter import scrolledtext
from PIL import Image, ImageTk
from ey_analytics.utils.logger import SetUpLogging
from ey_analytics.openai_api import OpenAI
from ey_analytics.utils.storage import Storage
from ey_analytics.cognitive_services import Speech, Vision


def start_video():
    # Create a VideoCapture object
    # '0' represents the default camera, you can change it if you have multiple cameras
    video = cv2.VideoCapture(0)

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


def save_frame(frame, image_name: str = "snapshot.jpg"):
    # Save the frame as an image file
    cv2.imwrite(image_name, frame)
    logging.info(f"Snapshot saved as {image_name}")


def frame_description(
    frame, container_name: str = "images", image_name: str = "snapshot.jpg"
):
    save_frame(frame, image_name)
    remote_image_url = storage.upload_image(
        container_name=container_name, image_name=image_name
    )
    image_analysis = vision.image_analyzer(remote_image_url)
    vision.check_image_analysis(image_analysis)
    image_description = image_analysis.caption.content
    return image_description


def format_conditions(conditions: tuple, format: str):
    if format == "Fala":
        return [item.capitalize() + "." for item in conditions]
    else:
        return conditions


def get_question(format: str):
    if format == "Interface":
        global user_input
        message = user_input.get()  # Obter a entrada do usuário
        logging.info("User: " + message)

    if format == "Fala":
        message = speech.speech_to_text()
    # else:
    #     message = input('Digite sua pergunta: ')

    # Exibir a mensagem do usuário na janela de chat
    chat_display.insert(tk.END, " " + "\n")
    chat_display.insert(tk.END, "User: " + message + "\n")

    return message


def respond(resposta: str, format: str):
    # Exibir a resposta do chatbot na janela de chat
    chat_display.insert(tk.END, "Bot: " + resposta + "\n")

    if format == "Interface":
        logging.info("Bot: " + resposta)
    if format == "Fala":
        speech.text_to_speech(resposta)


def clear_chat():
    chat_display.delete(1.0, tk.END)
    global previous_messages
    previous_messages = []


def store_messages(
    pergunta: str, resposta: str, previous_messages: list, previous_messages_limit: int
):
    previous_messages.append({"role": "user", "content": pergunta})
    previous_messages.append({"role": "assistant", "content": resposta})

    # Limitar armazenamento de últimas mensagens
    if len(previous_messages) > 2 * previous_messages_limit:
        del previous_messages[:2]

    return previous_messages


def send_message(
    perfil_sistema: str,
    format: str = "Interface",
    previous_messages: list = [],
    previous_messages_limit: int = 3,
    skip_response: str = False,
):
    # Pergunta
    pergunta = get_question(format)
    # pergunta = 'Imagine a cena a partir do que você vê'

    restart_conditions = format_conditions(
        ("limpar", "clear", "restart", "reiniciar", "limpe", "reinicie"), format
    )

    # Validar da pergunta
    if len(pergunta) == 0:
        resposta = "Desculpe, não entendi sua pergunta. Poderia repetir?"
        respond(resposta, format)
        skip_response = True
    elif pergunta in restart_conditions:
        clear_chat()
        skip_response = True
    elif ("gerar" or "imagem") in pergunta.lower():
        resposta = "Claro, me dê um instante"
        respond(resposta, format)
        openaiAPI.generate_image(pergunta)
        skip_response = True
    elif ("que você vê") in pergunta.lower():
        resposta = "Deixe me pensar por um momento"
        respond(resposta, format)
        video = start_video()
        frame = capture_frame(video, display=False)
        image_description = frame_description(frame)
        pergunta = f"{pergunta} Elabore uma pequena descrição para: {image_description}"

    if skip_response is False:
        # Gerar Resposta
        resposta = openaiAPI.ChatCompletion(
            perfil_sistema, pergunta, previous_messages=previous_messages
        )
        # Resposta
        respond(resposta, format)

    if ("imagine uma cena") in pergunta.lower():
        resposta = "Eu imagino a cena da seguinte maneira"
        respond(resposta, format)
        pergunta = f"{pergunta}: {resposta}"
        openaiAPI.generate_image(pergunta)

    # Tratar últimas mensagens
    previous_messages = store_messages(
        pergunta, resposta, previous_messages, previous_messages_limit
    )

    user_input.delete(0, tk.END)  # Limpar o campo de entrada


# Init logger
SetUpLogging().setup_logging()

# Init OpenAI
openaiAPI = OpenAI()

perfil_sistema = "Você é uma agente de inovação senior do mercado de técnologia chamada Faustina. Você tem amplo conhecimento sobre jogos, trabalhando para a empresa Ernest Young ou EY. As resposta devem ser formais e objetivas com no máximo 100 caracteres."

global previous_messages
previous_messages = []

# Init Speech
speech = Speech(
    recognition_language="pt-BR", synthesis_voice_name="pt-BR-GiovannaNeural"
)

# Init Vision
vision = Vision()

# Init Storage
storage = Storage()

window = tk.Tk()
window.title("GenAI Chatbot")
window.geometry("800x500")
window.configure(bg="#000000")  # "#f2f2f2"  # Cor de fundo da janela

# Configurar o comportamento responsivo
window.grid_rowconfigure(0, weight=1)
window.grid_rowconfigure(1, weight=0)
window.grid_columnconfigure(0, weight=1)
window.grid_columnconfigure(1, weight=0)

# Janela de chat
global chat_display  # Declarar a variável chat_display como global

chat_display = scrolledtext.ScrolledText(
    window,
    width=80,
    height=20,
    font=("Helvetica", 12),
    bg="#333333",  # "#ffffff",
    fg="#ffffff",  # "#333333",
    relief=tk.SUNKEN,
)
chat_display.grid(row=0, column=0, padx=15, pady=10, columnspan=4, sticky="nsew")

# Carregar a imagem do microfone
image_microphone = Image.open("microphone.png")

# Ajustar o tamanho da imagem conforme necessário
image_microphone = image_microphone.resize((24, 24))
photo_microphone = ImageTk.PhotoImage(image_microphone)

# Criar o botão com o logo de um microfone
microphone_button = tk.Button(
    window,
    image=photo_microphone,
    command=lambda: send_message(
        perfil_sistema, format="Fala", previous_messages=previous_messages
    ),
    relief=tk.FLAT,
)

microphone_button.grid(row=1, column=0, padx=5, pady=5, sticky="w")

# Entrada do usuário
user_input = tk.Entry(window, width=70, font=("Helvetica", 12), relief=tk.FLAT)
user_input.grid(row=1, column=1, padx=5, pady=5, sticky="w")

# Botão "Enviar"
send_button = tk.Button(
    window,
    text="Enviar",
    command=lambda: send_message(
        perfil_sistema, format="Interface", previous_messages=previous_messages
    ),
    bg="#4CAF50",
    fg="#ffffff",
    relief=tk.RAISED,
)
send_button.grid(row=1, column=2, padx=5, pady=5, sticky="w")

# Botão "Limpar"
clear_button = tk.Button(
    window,
    text="Limpar",
    command=clear_chat,
    bg="#FF0000",
    fg="#ffffff",
    relief=tk.RAISED,
)
clear_button.grid(row=1, column=3, padx=5, pady=5, sticky="w")

window.mainloop()
