import os
from flask import Flask, request, render_template, send_file, flash, redirect, url_for
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import io
import json
from django import forms
from ckeditor.fields import RichTextField
from fpdf import FPDF
from xhtml2pdf import pisa
from dotenv import load_dotenv
# import datetime
import bleach
from bs4 import BeautifulSoup
from bs4 import NavigableString

app = Flask(__name__, static_folder='static')
app.config['UPLOAD_FOLDER'] = 'uploads'  # Folder to save files before uploading to Google Drive
app.secret_key = 'supersecretkey'
 # Load environment variables from .env
load_dotenv()
# Load credentials from .env
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

# Convert JSON string to dictionary
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")
credentials_dict = json.loads(GOOGLE_CREDENTIALS)

# Create Google Credentials object
# Use `creds` wherever you need authentication
# Google Drive API setup
SCOPES = ['https://www.googleapis.com/auth/drive']
creds = service_account.Credentials.from_service_account_info(credentials_dict, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=creds)


# Define allowed tags and attributes
#allowed_tags = list(bleach.sanitizer.ALLOWED_TAGS) + ['p', 'strong', 'em', 'ul', 'li', 'ol']  # Convert to list before concatenation


# Google Drive folder ID where files will be uploaded

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    #sanitized_content = ""  # Initialize an empty string for sanitized content
    event_description = RichTextField()
    if request.method == 'POST':
        # Handle event inputs
        univ_name = request.form.get('univ_name', 'N/A')
        college_name = request.form.get('college_name', 'N/A')
        dropdown = request.form.get('dropdown', 'N/A')
        event_type = request.form.get('event_type', 'N/A')
        event_title = request.form.get('event_title', 'N/A')
        event_venue = request.form.get('event_venue', 'N/A')
        event_date = request.form.get('event_date', 'N/A')
        participant = request.form.get('participant', 'N/A')
        resource = request.form.get('resource', 'N/A')
        participant_count = request.form.get('participant_count', 'N/A')
        event_description = request.form.get('event_description')
        photo_desc = request.form.get('photo_desc', 'N/A')
        
         # Sanitize the input
        # sanitized_content = bleach.clean(event_description, tags=allowed_tags)

        # Create a dictionary to hold the event details
        event_data = {
            'Univ': univ_name,
            'College': college_name,
            'Dept': dropdown,
            'Event Type': event_type,
            'Event Title': event_title,
            'Event Venue': event_venue,
            'Event Date': event_date,
            'Photo Desc': photo_desc,
            'Participant': participant,
            'Resource': resource,
            'Participant Count': participant_count,
            'Description': event_description
        }

        # Handle the invitation image
        invitation_image = request.files.get("invitation_image")
        invitation_image_path = None
        if invitation_image:
            invitation_image_path = os.path.join(app.config['UPLOAD_FOLDER'], invitation_image.filename)
            invitation_image.save(invitation_image_path)
            upload_to_drive(invitation_image.filename, invitation_image_path)  # Upload image to Google Drive

        # Handle event photos (maximum 4)
        event_photos_paths = []
        image_files = request.files.getlist("photos[]")
        for image in image_files:
            if len(event_photos_paths) < 4:  # Limit to 4 images
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
                image.save(image_path)
                event_photos_paths.append(image_path)  # Store the path for PDF generation

                # Upload to Google Drive if necessary
                upload_to_drive(image.filename, image_path)  # You can modify this as needed

        # Generate the PDF from the event data and serve it in-memory
        pdf_bytes_io = create_pdf(event_data, invitation_image_path, event_photos_paths)

        # Save the PDF to a temporary file for uploading
        pdf_temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{event_data['Event Title']}_{event_data['Event Date']}.pdf")
        with open(pdf_temp_path, 'wb') as pdf_file:
            pdf_file.write(pdf_bytes_io.getvalue())

        # Upload the PDF to Google Drive
        upload_to_drive(f"{event_data['Event Title']}_{event_data['Event Date']}.pdf", pdf_temp_path)

        # Return the PDF for the user to view in the browser
        return send_file(
            pdf_bytes_io,
            mimetype='application/pdf',
            as_attachment=False,
            download_name=f"{event_data['Event Title']}_{event_data['Event Date']}.pdf"
        )
        
    return render_template('index.html')


class PDF(FPDF):
    def footer(self):
        # Set the position for the footer
        self.set_y(-15)
        self.set_text_color(0, 0, 0)
        self.set_font('DejaVu', 'I', 8)
        # Page number
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
        
def create_pdf(event_data, invitation_image_path, event_photos_paths):
    
    pdf = PDF()
    pdf.set_margins(left=10, top=10, right=10)
    pdf.add_font('DejaVu', '', 'fonts/ttf/DejaVuSans.ttf', uni=True)
    pdf.add_font('DejaVu', 'B', 'fonts/ttf/DejaVuSans-Bold.ttf', uni=True)  # Bold
    pdf.add_font('DejaVu', 'I', 'fonts/ttf/DejaVuSans-Oblique.ttf', uni=True)  # Italic
    pdf.add_font('DejaVu', 'BI', 'fonts/ttf/DejaVuSans-BoldOblique.ttf', uni=True)
    pdf.add_page()
    
    
    
    #university name
    pdf.set_font('DejaVu', 'B', 14)
    pdf.set_text_color(0, 0, 255)
    pdf.cell(0, 4, event_data['Univ'], ln=True, align='C')
    pdf.ln(3)
    
    #college name
    pdf.set_font('DejaVu', 'B', 13)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 4, event_data['College'], ln=True, align='C')
    pdf.ln(3)
    
    #dept name
    pdf.set_font('DejaVu', 'B', 12)
    pdf.cell(0, 4, event_data['Dept'], ln=True, align='C')
    pdf.ln(3)
    
    # Invitation Image
    if invitation_image_path:
        pdf.image(invitation_image_path, x=10, w=190,h=240)  # Adjust x and width as needed
        pdf.ln(5)
    
    
    #university name
    pdf.set_font('DejaVu', 'B', 14)
    pdf.set_text_color(0, 0, 255)
    pdf.cell(0, 4, event_data['Univ'], ln=True, align='C')
    pdf.ln(3)
    
    #college name
    pdf.set_font('DejaVu', 'B', 13)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 4, event_data['College'], ln=True, align='C')
    pdf.ln(3)
    
    #dept name
    pdf.set_font('DejaVu', 'B', 12)
    pdf.cell(0, 4, event_data['Dept'], ln=True, align='C')
    pdf.ln(3)
    
    # Event Title
    pdf.set_font('DejaVu', 'B', 12)
    pdf.cell(0, 6,f"A Report on", ln=True, align='C')
    pdf.cell(0, 6,event_data['Event Title'], ln=True, align='C')
    pdf.ln(3)  # Line break
    
    #type of the event
    pdf.set_font('DejaVu', '', 11)
    pdf.cell(0, 4, f"Type: {event_data['Event Type']}", ln=True)
    pdf.ln(3)
    
    # Date 
    pdf.set_font('DejaVu', '', 11)
    pdf.cell(0, 4, f"Date: {event_data['Event Date']}", ln=True)
    pdf.ln(3)
    
    # venue
    pdf.set_font('DejaVu', '', 11)
    pdf.cell(0, 4, f"Venue: {event_data['Event Venue']}", ln=True)
    pdf.ln(3)

    
    
    if event_data['Resource']:
        # Calculate the width of the participant's name
        participant_name = event_data['Participant']
        link_width = pdf.get_string_width(participant_name)
        # Participant
        pdf.cell(0,6,f"Participant:",ln=True)
        # pdf.set_text_color(0, 0, 255)
        pdf.cell(link_width,4,event_data['Participant'],link=event_data['Resource'], ln=False)
        pdf.set_text_color(255, 60, 0)
        pdf.cell(0,4, " (click the name to check out their LinkedIn Profile)", ln=True)
        pdf.ln(3)
    else:
        pdf.set_font('DejaVu', '', 11)
        pdf.cell(0, 4, f"Participant: {event_data['Participant']}", ln=True)
        pdf.ln(3)
    
    
    # Participant resource link
    pdf.set_font('DejaVu', 'I', 11)
    pdf.cell(0, 6, f"Participant's LinkedIn",link=event_data['Resource'], ln=True)
    pdf.ln(3)

    # Participant Count
    pdf.set_font('DejaVu', '', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 5, f"Participant Count: {event_data['Participant Count']}", ln=True)
    pdf.ln(3)

    # Parse the HTML content using BeautifulSoup
    content = BeautifulSoup(event_data['Description'], 'html.parser')

    # About the Event
    pdf.set_font('DejaVu', '', 11)
    pdf.cell(0,6,f"About the Event:",ln=True)
    #pdf.multi_cell(0, 4, content)
    
    # Function to set the font based on HTML tags
    def set_font_style(tag=None):
        if tag == 'b':
            pdf.set_font('DejaVu', 'B', 11)  # Bold
        elif tag == 'i':
            pdf.set_font('DejaVu', 'I', 11)  # Italic
        elif tag == 'b' and 'i':  # Handle bold italic combo
            pdf.set_font('DejaVu', 'BI', 11)  # Bold Italic
        else:
            pdf.set_font('DejaVu', '', 11)  # Regular font

    # Function to recursively handle HTML content and apply styles
    def process_element(element):
        if isinstance(element, NavigableString):
            text = element.strip()
            if text:  # Avoid empty strings
                pdf.multi_cell(0, 6, text)
        elif element.name == 'b':
            pdf.set_font('DejaVu', 'B', 11)
            pdf.multi_cell(0, 6, element.text)
            pdf.set_font('DejaVu', '', 11)
        elif element.name == 'i':
            pdf.set_font('DejaVu', 'I', 11)
            pdf.multi_cell(0, 6, element.text)
            pdf.set_font('DejaVu', '', 11)
        elif element.name == 'br':
            pdf.ln(5)
        elif element.name == 'p':
            pdf.multi_cell(0, 6, element.text)
            pdf.ln(5)
        elif element.name == 'ul':
            for li in element.find_all('li'):
                pdf.multi_cell(0, 6, f'• {li.text}')
                pdf.ln(5)
        elif element.name == 'ol':
            for idx, li in enumerate(element.find_all('li'), 1):
                pdf.multi_cell(0, 6, f'{idx}. {li.text}')
                pdf.ln(5)
        else:
            #Check if element has children before looping
            if hasattr(element, "children"):
                for child in element.children:
                    process_element(child)  #Recursively process elements

    # Process the HTML content safely
    for element in content.children:
        if not isinstance(element, NavigableString):  # Skip plain text
            process_element(element)
    

    # Photos of Event
    pdf.set_font('DejaVu', 'B', 12)
    pdf.cell(0, 10, "Event Photos", ln=True)
    pdf.set_font('DejaVu', '', 11)
    
    #photo descritpion
    image_desc = event_data['Photo Desc'].split(',')

    # Uniform size for all photos
    uniform_width = 190
    uniform_height = 100
    
    for i, photo_path in enumerate(event_photos_paths):
        pdf.image(photo_path, x=(pdf.w - uniform_width) / 2, w=uniform_width, h=uniform_height) # Adjust x and width as needed
        pdf.ln(3)
        pdf.set_font('DejaVu', '', 10)  # Set the font for the description text
        pdf.multi_cell(0, 6,f"({image_desc[i].strip()})",align='C')
        pdf.ln(10)
    
    
    pdf_bytes_io = io.BytesIO()
    pdf_bytes_io.write(pdf.output(dest='S').encode('latin1'))
    pdf_bytes_io.seek(0)

    return pdf_bytes_io

def upload_to_drive(file_name, file_path):
    """Uploads a file to Google Drive and stores it in the specific folder."""
    try:
        # File metadata with the specific folder ID
        file_metadata = {
            'name': file_name,
            'parents': [GOOGLE_DRIVE_FOLDER_ID]  # Upload to the specified folder
        }
        media = MediaFileUpload(file_path, resumable=True)  # Set resumable=True to handle large files

        # Create a file in Google Drive
        uploaded_file = drive_service.files().create(
            body=file_metadata, 
            media_body=media, 
            fields='id'
        ).execute()

       # Return the file ID upon success
        file_id = uploaded_file.get('id')
        if file_id:
            print(f"File uploaded successfully: {file_id}")
            return file_id  # Return file ID upon success
        else:
            return None  # Return None in case of failure
    except Exception as e:
        print(f"An error occurred while uploading to Google Drive: {e}")
        return None
     
@app.route("/healthz")
def health_check():
    return "OK", 200  # Must return status 200


if __name__ == '__main__':
    from waitress import serve
    serve(app, host="0.0.0.0", port=10000)
    # Ensure the upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    app.run(debug=True)
