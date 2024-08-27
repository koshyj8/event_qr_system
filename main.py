import qrcode
import uuid
import gspread
import mysql.connector
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
import os
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv, dotenv_values
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import time
load_dotenv()

def generate_coupon_with_serial(serial_number, output_filename):
    template = Image.open("coupon_template.png") 
    draw = ImageDraw.Draw(template)

    font = ImageFont.truetype("arial.ttf", 36)  
    text_position = (150, 200)  
    draw.text(text_position, serial_number, font=font, fill="black")
    template.save(output_filename)


def generate_qr_code(data, filename):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)
    
import traceback

def send_email(to_email, qr_filename, coupon_filename, id, name, phone, enrollment_no):
    from_email = os.getenv("email_id")
    password = os.getenv("email_app_pw")

    if not password:
        print(f"Error: Email app password not set in environment variables.")
        return

    subject = "🎉 Your QR Code for Aavesham'24! 🎉"

    body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .header {{ font-size: 20px; font-weight: bold; color: #333; }}
            .details {{ margin: 20px 0; }}
            .details ul {{ list-style-type: none; padding: 0; }}
            .details li {{ margin-bottom: 10px; }}
            .footer {{ margin-top: 20px; }}
        </style>
    </head>
    <body>
        <p class="header">Dear {name},</p>

        <p>We are thrilled to share with you your unique QR code for <strong>Aavesham'24</strong>! 🎊</p>

        <hr />

        <p class="header">🎫 Your Details</p>

        <div class="details">
            <ul>
                <li><strong>Name:</strong> {name}</li>
                <li><strong>ID No.:</strong> {id}</li>
                <li><strong>Enrollment No.:</strong> {enrollment_no}</li>
                
                <li><strong>Phone Number:</strong> {phone}</li>
            </ul>
        </div>

        <p>Use the attached QR code to avail a delightful <strong>Sadhya</strong> at Aavesham'24!</p>

        <hr />

        <p class="footer">
            We look forward to seeing you at the event. If you have any questions or need further assistance, feel free to reach out to any Malayali on campus :).<br><br>
            Best regards,<br>
            <strong>VNIT Malayali Association</strong>
        </p>
    </body>
    </html>
    """
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    try:
        with open(qr_filename, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(qr_filename)}')
            msg.attach(part)
        
        """with open(coupon_filename, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(coupon_filename)}')
            msg.attach(part)"""

    except FileNotFoundError:
        print(f"Error: File not found.")
        return
    except Exception as e:
        print(f"Error attaching files: {str(e)}")
        return

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        print(f"Email sent successfully to {to_email} with QR code {qr_filename} and coupon {coupon_filename}")
    except smtplib.SMTPAuthenticationError:
        print(f"SMTP Authentication failed. Please check your email and app password.")
    except smtplib.SMTPException as e:
        print(f"SMTP error occurred: {str(e)}")
    except Exception as e:
        print(f"Failed to send email to {to_email}. Error: {str(e)}")
        print("Traceback:")
        print(traceback.format_exc())

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)

if creds and creds.expired and creds.refresh_token:
    creds.refresh(Request())

client = gspread.authorize(creds)

sheet = client.open('ONAM24 SADHYA REGISTRATION (Responses)').sheet1

records = sheet.get_all_records()
print(f"Retrieved {len(records)} records from the sheet.")
headers = sheet.row_values(1)
first_empty_col = len(headers) + 1
if not os.path.exists('qr_codes'):
    os.makedirs('qr_codes')

if "Unique ID" not in headers:
    sheet.update_cell(1, first_empty_col, "Unique ID")
    headers.append("Unique ID")
    first_empty_col += 1
if "Sadhya Used" not in headers:
    sheet.update_cell(1, first_empty_col, "Sadhya Used")
    headers.append("Sadhya Used")
    first_empty_col += 1
if "Coupon Serial" not in headers:
    sheet.update_cell(1, first_empty_col, "Coupon Serial")
    headers.append("Coupon Serial")
    first_empty_col += 1

batch_size = 10
batch_delay = 60

for i, record in enumerate(records):
    try:
        print(f"Processing record: {record}")
        
        id_no = str(record['ID No.'])
        print(f"ID No.: {id_no}")

        cell = sheet.find(id_no)
        row = cell.row
        unique_id_cell = sheet.cell(row, headers.index("Unique ID") + 1)
        unique_id = unique_id_cell.value

        if unique_id:
            print(f"Record with ID No. {id_no} already exists with Unique ID {unique_id}. Skipping.")
            
        elif id_no == '':
            print('')
            
        else:
            unique_id = str(uuid.uuid4())
            qr_data = unique_id
            qr_filename = f"qr_codes/{id_no}.png"
            generate_qr_code(qr_data, qr_filename)
            sheet.update_cell(row, headers.index("Unique ID") + 1, unique_id)
            sheet.update_cell(row, headers.index("Sadhya Used") + 1, "FALSE")

            serial_number = str(uuid.uuid4())[:8].upper()
            coupon_filename = f"coupons/{id_no}_coupon.png"
            generate_coupon_with_serial(serial_number, coupon_filename)
            sheet.update_cell(row, headers.index("Coupon Serial") + 1, serial_number)


            send_email(record['Email'], qr_filename, coupon_filename, str(record['ID No.']), record['Name'], record['Phone Number'], record['Enrollment No.'])
    except Exception as e:
        print(f"Error processing record {i+1}: {str(e)}")
        print("Traceback:")
        print(traceback.format_exc())
        continue
    if (i + 1) % batch_size == 0:
        print(f"Batch {i // batch_size + 1} complete. Sleeping for {batch_delay} seconds.")
        time.sleep(batch_delay)

print("QR codes generated, emails sent, and sheet updated successfully!")