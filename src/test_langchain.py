import os
import time
import logging
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import ElasticVectorSearch, FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import AzureOpenAI
from EYAnalytics.utils.speechAPI import Speech
from EYAnalytics.utils.logger import SetUpLogging

# Init logger
SetUpLogging().setup_logging()

load_dotenv(dotenv_path=os.path.abspath('./.azure/.env'))

OPENAI_GPT_DEPLOYMENT = os.environ.get(
    "OPENAI_GPT_DEPLOYMENT") or "text-davinci-003"

# Init Speech
speech = Speech(recognition_language='pt-BR',
                synthesis_voice_name='pt-BR-FranciscaNeural')


@SetUpLogging.function_logger
def read_pdf_file(pdf_file_name: str):
    logging.info('Lendo Arquivo: ' + pdf_file_name)
    pdf_file_path = os.path.abspath('./samples/pdf/' + pdf_file_name)

    return PdfReader(pdf_file_path)


@SetUpLogging.function_logger
def pdf_to_text(pdf_file):
    # Read data from the file and put them into a variable called raw_text
    raw_text = ''

    for i, page in enumerate(pdf_file.pages):
        text = page.extract_text()
        if text:
            raw_text += text
    logging.info('Total de caracteres: ' + str(len(raw_text)))

    return raw_text


@SetUpLogging.function_logger
def text_splitter(raw_text: str):
    # We need to split the text that we read into smaller chunks
    # so that during information retrieval we don't hit the token size limit

    logging.info('Particionando texto')

    text_splitter = CharacterTextSplitter(
        separator='\n',
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )

    return text_splitter.split_text(raw_text)


@SetUpLogging.function_logger
def config_docsearch(texts):
    logging.info('Configurando Docsearch')
    # Download embeddings from OpenAI
    embeddings = OpenAIEmbeddings(
        model=OPENAI_GPT_DEPLOYMENT, chunk_size=1, max_retries=10)
    docsearch = FAISS.from_texts(texts, embeddings)
    return docsearch


@SetUpLogging.function_logger
def config_chain(chain_type: str = "stuff"):
    logging.info('Configurando Chain')
    llm = AzureOpenAI(deployment_name=OPENAI_GPT_DEPLOYMENT)
    chain = load_qa_chain(llm, chain_type=chain_type)
    return chain


def demo(docsearch, chain):
    # Demo
    message = "Quais empresas venceram as categorias de AI e Analytics?"
    docs = docsearch.similarity_search(message)
    response = chain.run(input_documents=docs, question=message)

    print(" ")
    print("Pergunta: ", message)
    print("Resposta: ", response)


@SetUpLogging.function_logger
def chatbot(docsearch, chain, mode: str = 'Texto'):
    def mode_message(mode: str):
        try:
            if mode in ['Texto', 'Text', 'texto']:
                return input("Digite sua pergunta: ")
            elif mode in ['Fala', 'Speech', 'fala']:
                time.sleep(1)
                input("Pressione Enter para perguntar...")
                return speech.speech_to_text()

        except ValueError as exception:
            logging.error('Inclua um valor de modalidade válido')
            print(exception)

    def mode_response(mode: str, response: str):
        try:
            if mode in ['Texto', 'Text', 'texto']:
                return print("Resposta: ", response)
            elif mode in ['Fala', 'Speech', 'fala']:
                return speech.text_to_speech(response)
        except ValueError as exception:
            logging.error('Inclua um valor de modalidade válido')
            print(exception)

    logging.info('Iniciando Chatbot')
    logging.info('Modo: ' + mode)

    exit_conditions = (":q", "quit", "exit", "sair", "pare",
                       "parar", "Sair", "Sair.", "Encerrar.")

    # Define System Chatbot
    system = 'Responda em português com resposta curtas e objetivas, entre 30 e 50 palavras'

    # Run Demo
    demo(docsearch, chain)

    # Question & Answer Conversation
    while True:
        print(" ")
        message = mode_message(mode)
        if len(message) == 0:
            texto = "Desculpe, não entendi. Poderia repetir?"
            speech.text_to_speech(texto)
            continue
        elif message in exit_conditions:
            logging.info('Encerrando Chatbot')
            break

        docs = docsearch.similarity_search(message)
        response = chain.run(input_documents=docs, question=system + message)
        mode_response(mode, response)
        print(" ")


def main(pdf_file_name, chatbot_mode):

    pdf_file = read_pdf_file(pdf_file_name)

    raw_text = pdf_to_text(pdf_file)

    texts = text_splitter(raw_text)

    # Configura Indexador
    docsearch = config_docsearch(texts)

    # Configura LLM
    chain = config_chain()

    # Start Chatbot
    chatbot(docsearch, chain, chatbot_mode)


if __name__ == '__main__':
    pdf_file_name = 'OnePage - 2022 Microsoft Partner of the Year Awards Winners.pdf'
    chatbot_mode = 'fala'
    main(pdf_file_name, chatbot_mode)
