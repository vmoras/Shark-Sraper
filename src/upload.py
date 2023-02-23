import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
import socket


class Uploader:

    @staticmethod
    def upload() -> None:
        """
        Uploads videos to a google drive folder.
        """
        # Set the main variables such as the service to be used and paths
        service = Uploader._create_service()
        folder_id = "1nFJZVdlnYMNqgCFLLi3TEgqkFgS7yBEh"
        directory = "./images_raw"
        directory = "./upload"

        #folder_id = "1dxW6izWM2j9E44lnU4hCAij5RQFVFI0Q"
        #directory = "./images_label"

        # Know how many files will be uploaded
        lst = os.listdir(directory)
        total_files = len(lst)
        num_file = 1

        # Iterate over each video in the given directory
        for video in os.listdir(directory):
            filename = os.fsdecode(video)
            file_metadata = {
                "name": filename,
                "parents": [folder_id]
            }
            path = f"{directory}/{filename}"
            media = MediaFileUpload(path, mimetype="image/png", resumable=True)

            # Upload video
            try:
                service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields="id"
                ).execute()

            except HttpError as error:
                print(f'An error occurred: {error}')

            print(f"Uploaded file: {num_file}/{total_files}")
            num_file += 1

    @staticmethod
    def _create_service():
        """
        Returns a resource object with methods for interacting with the service
        """
        # What permissions the program has and the credentials to access to Google Drive
        SCOPES = ['https://www.googleapis.com/auth/drive.file']
        credentials = "lib/credentials.json"

        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('lib/token.json'):
            creds = Credentials.from_authorized_user_file('lib/token.json', SCOPES)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials, SCOPES)
                creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open('lib/token.json', 'w') as token:
                token.write(creds.to_json())

        # Built service
        try:
            # Set timeout to 10 minutes
            socket.setdefaulttimeout(600)

            service = build('drive', 'v3', credentials=creds)
            return service

        except HttpError as error:
            print(f'An error occurred: {error}')
