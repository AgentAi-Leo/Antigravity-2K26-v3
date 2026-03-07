import json

audio_url = "https://kieai.redpandaai.co/api/file-base64-upload/12345.m4a"
task_input = {"audio_url": [audio_url]}
task_body = {
    "model": "elevenlabs/speech-to-text",
    "input": task_input
}
print(json.dumps(task_body))
print(type(task_body["input"]["audio_url"]))
