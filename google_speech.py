import speech_recognition as sr

def recognize_speech_from_mic(lang):
    recognizer = sr.Recognizer()
    mic = sr.Microphone(device_index=1)
    # check that recognizer and microphone arguments are appropriate type
    if not isinstance(recognizer, sr.Recognizer):
        raise TypeError("`recognizer` must be `Recognizer` instance")

    if not isinstance(mic, sr.Microphone):
        raise TypeError("`microphone` must be `Microphone` instance")

    # adjust the recognizer sensitivity to ambient noise and record audio
    # from the microphone
    with mic as source:
        recognizer.energy_threshold = 10
        recognizer.pause_threshold = 1
        recognizer.adjust_for_ambient_noise(source) # #  analyze the audio source for 1 second
        print("Start")
        audio = recognizer.listen(source)
        print("End")
    # set up the response object
    response = {
        "success": True,
        "error": None,
        "transcription": None
    }

    # try recognizing the speech in the recording
    # if a RequestError or UnknownValueError exception is caught,
    #   update the response object accordingly
    try:
        response["transcription"] = recognizer.recognize_google(audio, language=lang)
    except sr.RequestError:
        # API was unreachable or unresponsive
        response["success"] = False
        response["error"] = "API unavailable/unresponsive"
    except sr.UnknownValueError:
        # speech was unintelligible
        response["error"] = "Unable to recognize speech"

    return response['transcription']

if __name__ == "__main__":

    response = recognize_speech_from_mic('en-US')
    print(response)
