from uuid import uuid4

import requests
from io import BytesIO
from pydub import AudioSegment


def get_audio_from_url(audio_url):
    # Step 1: Download the audio file from the URL
    response = requests.get(audio_url)

    # Check if the request was successful
    if response.status_code == 200:
        # Step 2: Load the content into a BytesIO object
        audio_file = BytesIO(response.content)

        # Step 3: Load the audio into AudioSegment
        audio_segment = AudioSegment.from_file(audio_file, format="wav")

        return audio_segment
    else:
        raise Exception(f"Failed to download audio from {audio_url}. Status code: {response.status_code}")


def combine_audio_files(summaries_without_podcast):
    # Concatenate audio files from summaries
    combined_audio = None
    for summary in summaries_without_podcast:
        audio_segment = get_audio_from_url(f"http://localhost:8000/static/audio/{summary.id}.wav")
        if combined_audio is None:
            combined_audio = audio_segment
        else:
            combined_audio += audio_segment

    # If combined_audio is still None, there were no valid audio files
    if combined_audio is None:
        raise ValueError("No valid audio files to concatenate.")

    # Save the concatenated audio to a new file (e.g., MP3 format)
    new_podcast_filename = f"./summarize/static/audio/podcast_episode_{uuid4()}.mp3"
    combined_audio.export(new_podcast_filename, format="mp3")
    return new_podcast_filename.replace("./summarize", "")
