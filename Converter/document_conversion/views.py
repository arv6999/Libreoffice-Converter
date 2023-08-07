from django.http import HttpResponse
from django.shortcuts import render
from django.core.files.storage import default_storage
import subprocess
import os
from django.conf import settings


def upload_file(request):
    if request.method == 'POST' and request.FILES['document']:
        document = request.FILES['document']
        file_path = handle_uploaded_file(document)

        # Convert the document to PDF and upload to S3
        converted_url = convert_and_upload_to_s3(file_path)

        return render(request, 'success.html', {'download_url': converted_url})

    return render(request, 'upload.html')


def handle_uploaded_file(document):
    file_path = os.path.join(settings.MEDIA_ROOT, document.name)
    with open(file_path, 'wb+') as destination:
        for chunk in document.chunks():
            destination.write(chunk)
    return file_path


def convert_and_upload_to_s3(file_path):
    # Convert the document to PDF using LibreOffice
    pdf_path = file_path.rsplit('.', 1)[0] + '.pdf'
    command = ['libreoffice', '--headless', '--convert-to',
               'pdf', '--outdir', settings.MEDIA_ROOT, file_path]
    subprocess.run(command)

    # Upload the converted document to S3
    converted_file = open(pdf_path, 'rb')
    converted_url = default_storage.save(pdf_path, converted_file)
    converted_file.close()

    # Remove the temporary PDF file
    os.remove(pdf_path)

    # Return the S3 object URL
    return default_storage.url(converted_url)


def download_file(request, download_url):
    response = HttpResponse()
    response['Content-Disposition'] = 'attachment; filename="converted_document.pdf"'
    response['X-Sendfile'] = download_url
    return response
