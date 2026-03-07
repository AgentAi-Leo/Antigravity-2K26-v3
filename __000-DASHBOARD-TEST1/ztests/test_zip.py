import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app
import io
import zipfile

audio = [{"name": "test.mp3", "transcript": "hello world"}]
b = app.generate_zip_of_all_transcripts(audio, "PDF (.pdf)")
z = zipfile.ZipFile(io.BytesIO(b))
print("PDF ZIP contains:", z.namelist())

b2 = app.generate_zip_of_all_transcripts(audio, "DOC (.doc)")
z2 = zipfile.ZipFile(io.BytesIO(b2))
print("DOC ZIP contains:", z2.namelist())
