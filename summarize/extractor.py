## clone from https://github.com/amscotti/page-summarizer/blob/main/app.py

import argparse
import os
import sys
from urllib.parse import urlparse

import html2text
import replicate
import requests
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.prompts import ChatPromptTemplate
from langchain_community.document_loaders import PyPDFLoader, YoutubeLoader
from langchain_openai import ChatOpenAI
import structlog
from environs import Env

logger = structlog.get_logger()

env = Env()
test_extract = env.bool("TEST_EXTRACT", True)
test_summary = env.bool("TEST_SUMMARY", True)


MODEL_NAME = "gpt-4o-mini"
SUMMARY_TEMPLATE = """
You are tasked with writing a comprehensive summary the following text so that readers will have a full understanding of the text, without need of referencing the source material.
Your summary should reflect the length of the source material, and provide enough details, that the reader can fully understand the subject and speak of it at a high-level.
You will also providing list of 3 or more brief key points from the article that may not be covered by the initial report, additional key points can be keep together under 'KEY POINTS'.

{text}

Use the format,

<Title>:
<Summary>

KEY POINTS:
- <Key Point>
- <Key Point>
- <Key Point>
- ...
"""

SUMMARY_PROMPT = ChatPromptTemplate.from_template(SUMMARY_TEMPLATE)

h = html2text.HTML2Text()
h.ignore_links = True

YOUTUBE_URLS = ["www.youtube.com", "youtube.com", "youtu.be"]


def extract_text_from_url(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        "Content-Type": "text/html; charset=UTF-8",
    }
    response = requests.get(url, headers=headers)
    return h.handle(response.text)


def extract_text_from_pdf(url: str) -> str:
    loader = PyPDFLoader(url)
    return loader.load()


def extract_text_from_youtube(url: str) -> str:
    loader = YoutubeLoader.from_youtube_url(url, add_video_info=False)
    return loader.load()


def extract_text(source: str) -> str:
    if test_extract:
        return """
        I'm the content of a webpage hahaha.
        """
    try:
        parsed_url = urlparse(source)
        if parsed_url.netloc in YOUTUBE_URLS:
            return extract_text_from_youtube(source)
        elif parsed_url.path.endswith(".pdf"):
            return extract_text_from_pdf(source)
        else:
            return extract_text_from_url(source)
    except requests.exceptions.RequestException as e:
        logger.debug(f"An error occurred while trying to fetch the text: {e}")
        sys.exit(2)


def get_summary(text: str) -> str:
    if test_summary:
        return """
        The shift towards running artificial intelligence (AI) models locally, particularly on personal laptops, represents a notable trend in technology usage among researchers. Historically, large language models (LLMs) were predominantly accessed online, utilizing substantial parameters to perform complex functions. However, advancements in technology have enabled organizations to develop open-weight models which are download-friendly and can operate on standard consumer hardware. This evolution allows researchers to utilize robust AI tools without relying on cloud-based services.\n\nBioinformatician Chris Thorpe exemplifies this movement, utilizing local AI to process and summarize immunological data, thus safeguarding patient confidentiality and adhering to regulatory standards. The growing accessibility of smaller models—like those created by companies such as Google DeepMind and Meta—enables researchers to enhance their workflow significantly. These models, despite being less extensive than their predecessors, offer impressive performance and are conducive to scientific tasks. \n\nPrivacy emerges as a critical factor driving the preference for local models. Many professionals, including healthcare practitioners, are concerned about the implications of transmitting sensitive data to cloud-based AI services. Local models allow for maintaining data integrity while providing functionalities like training new models, generating insights from medical data, and automating tedious tasks such as summarizing patient conversations.\n\nThorpe and fellow researchers appreciate local AIs' ability to provide a stable and reproducible environment, which is often compromised by the commercial model updates they would otherwise rely upon. Furthermore, the software landscape for running these models has become increasingly user-friendly, with several platforms facilitating model downloads and usage across multiple operating systems. The ongoing development in local LLMs is promising, providing researchers with tools that enhance autonomy, foster innovation, and protect data privacy.\n\n**KEY POINTS:**\n- The rise of open-weight models has democratized access to powerful LLMs, enabling researchers with standard hardware to run these models locally.\n- Local AIs offer significant privacy benefits, especially in fields like healthcare, where maintaining patient confidentiality is paramount.\n- The local model landscape allows for greater control over reproducibility and stability in research projects, in contrast to the variability associated with commercial cloud-based AI services.\n- Tools like Ollama and GPT4All simplify the process of running LLMs on personal computers, making AI accessible to a wider audience across various scientific disciplines."
        """
    chain = SUMMARY_PROMPT | ChatOpenAI(
        temperature=1,
        model_name=MODEL_NAME,
        streaming=False,
        callbacks=[StreamingStdOutCallbackHandler()],
    )
    response = chain.invoke({"text": text})
    logger.info(response.content)
    return response.content


def generate_audio(summary: str) -> str:
    input = {
        "speaker": "https://replicate.delivery/pbxt/Jt79w0xsT64R1JsiJ0LQRL8UcWspg5J4RFrU6YwEKpOT1ukS/male.wav",
        "text": summary,
    }

    url = replicate.run(
        "lucataco/xtts-v2:684bc3855b37866c0c65add2ff39c78f3dea3f4ff103a436465326e0f438d55e",
        input=input
    )
    return url


def generate_and_save_audio(summary: str, filename: str) -> None:
    audio_url = generate_audio(summary)
    response = requests.get(audio_url, stream=True)

    # Open the file in write-binary mode and write the content to it
    with open(f"summarize/static/audio/{filename}.wav", 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):  # Download in chunks
            file.write(chunk)
            

def make_summary(url: str) -> str:
    text = extract_text(url)
    return get_summary(text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="The URL to create a summary from")
    args = parser.parse_args()

    summary = get_summary(extract_text(args.url))
    audio_url = generate_audio(summary)
    # Send a GET request to the URL
    response = requests.get(audio_url, stream=True)

    # Open the file in write-binary mode and write the content to it
    with open("summarize/static/audio/test.wav", 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):  # Download in chunks
            file.write(chunk)

    print(f"File downloaded as test.wav from {audio_url}")


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("Error: The OPENAI_API_KEY environment variable is not set.")
        sys.exit(1)

    main()
