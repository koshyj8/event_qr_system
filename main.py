import qrcode
import uuid
import gspread
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
import os
from dotenv import load_dotenv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import traceback
import random
import string

load_dotenv()

def generate_qr_code(data, filename):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)

def generate_serial_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def send_email(to_email, qr_filename, id, name, phone, enrollment_no, serial_code):
    from_email = os.getenv("email_id")
    password = os.getenv("email_app_pw")

    if not password:
        print(f"Error: Email app password not set in environment variables.")
        return

    subject = "🎉 Your QR Code for Aavesham'24! 🎉"
    body = f"""

            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .header {{ font-size: 20px; font-weight: bold; color: #333; }}
                    .details {{ margin: 20px 0; }}
                    .details ul {{ list-style-type: none; padding: 0; }}
                    .details li {{ margin-bottom: 10px; }}
                    .footer {{ margin-top: 20px; }}
                    .offers {{ background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin-top: 20px; }}
                </style>
            </head>
            <body>
                <p class="header">Dear {name},</p>
                <p>We are thrilled to share with you your QR code for <strong>Aavesham'24</strong>! 🎊</p>
                <hr />
                <p class="header">🎫 Your Details</p>
                <div class="details">
                    <ul>
                        <li><strong>Name:</strong> {name}</li>
                        <li><strong>ID No.:</strong> {id}</li>
                        <li><strong>Enrollment No.:</strong> {enrollment_no}</li>
                        <li><strong>Phone Number:</strong> {phone}</li>
                        <li><strong>Aarohi Discount Code:</strong> {serial_code}</li>
                    </ul>
                </div>
                <p>Use the attached QR code to avail a delightful <strong>Sadhya</strong> at Aavesham'24!</p>
                <hr />
                <div class="offers">
                    <p><strong>Special Discounts & Offers:</strong></p>
                    <ul>
                        <li>Show your unique Aarohi Serial Number during Aarohi registration to avail 20% discount on Tickets.</li>
                        <li>Don't forget to collect your coupons for exclusive discounts and offers at Anna Idli, Cluckers, Giani Ice Cream, and TumbleDry from the Sadhya counter on 22nd September 2024.</li>
                    </ul>
                </div>
                <p class="footer">
                    We look forward to seeing you at the event. If you have any questions or need further assistance, feel free to reach out to <a href="mailto:gokulravivarma3@gmail.com">gokulravivarma3@gmail.com</a> or call 9496521841 :).<br><br>
                    Best regards,<br>
                    <strong>VNIT Malayali Association</strong>
                </p>
            </body>
            </html>    """
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
        print(f"Email sent successfully to {to_email} with QR code {qr_filename}")
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
sheet = client.open('Onam Celebration Data').sheet1

records = sheet.get_all_records(expected_headers = ["Unique ID", "Sadhya Used", "Serial Code", "Name", "ID No.", "Enrollment No.", "Phone Number", "Email"])
print(f"Retrieved {len(records)} records from the sheet.")
headers = sheet.row_values(1)
first_empty_col = len(headers) + 1
if not os.path.exists('qr_codes'):
    os.makedirs('qr_codes')

required_columns = ["Unique ID", "Sadhya Used", "Serial Code"]
for col in required_columns:
    if col not in headers:
        sheet.update_cell(1, first_empty_col, col)
        headers.append(col)
        first_empty_col += 1

n = int(input("Enter no. of records to process: "))
processed_count = 0

unique_id_column = headers.index("Unique ID") + 1
serial_code_column = headers.index("Serial Code") + 1
unique_ids = sheet.col_values(unique_id_column)
last_processed_row = max(i for i, unique_id in enumerate(unique_ids) if unique_id != "") + 1

for row in range(last_processed_row + 1, sheet.row_count + 1):
    if processed_count >= n:
        break
    
    try:
        record = {header: sheet.cell(row, headers.index(header) + 1).value for header in headers}
        print(f"Processing record: {record}")
        
        id_no = str(record['ID No.'])
        print(f"ID No.: {id_no}")
        
        unique_id_cell = sheet.cell(row, unique_id_column)
        unique_id = unique_id_cell.value
        
        if unique_id:
            print(f"Record with ID No. {id_no} already exists with Unique ID {unique_id}. Skipping.")
        elif id_no == '':
            print('Empty ID No. Skipping.')
        else:
            unique_id = str(uuid.uuid4())
            qr_data = unique_id
            qr_filename = f"qr_codes/{id_no}.png"
            generate_qr_code(qr_data, qr_filename)            
            serial_code = generate_serial_code()
            send_email(record['Email'], qr_filename, id_no, record['Name'], record['Phone Number'], record['Enrollment No.'], serial_code)
            sheet.update_cell(row, unique_id_column, unique_id)
            sheet.update_cell(row, serial_code_column, serial_code)
            sheet.update_cell(row, headers.index("Sadhya Used") + 1, "FALSE")            
            processed_count += 1        
    except Exception as e:
        print(f"Error processing record in row {row}: {str(e)}")
        print("Traceback:")
        print(traceback.format_exc())
        continue
    
print(f"Processed {processed_count} records.")
