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
import time

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
                        <li>Show your unique Aarohi Serial Number during Aarohi registration to avail 10% discount on Tickets.</li>
                        <li>Don't forget to collect your coupons for exclusive discounts and offers at Anna Idli, Cluckers, and Giani Ice Cream from the Sadhya counter on 22nd September 2024.</li>
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

def fetch_all_data():
    records = sheet.get_all_records(expected_headers = ["Unique ID", "Sadhya Used", "Serial Code", "Name", "ID No.", "Enrollment No.", "Phone Number", "Email"])
    return records

def batch_update(updates):
    sheet.batch_update(updates)

def exponential_backoff(func, max_retries=5):
    for n in range(max_retries):
        try:
            return func()
        except gspread.exceptions.APIError as e:
            if e.response.status_code == 429:
                time.sleep((2 ** n) + random.random())
            else:
                raise
    raise Exception("Max retries exceeded")

def get_column_index(header_name):
    headers = sheet.row_values(1)
    try:
        return headers.index(header_name) + 1
    except ValueError:
        print(f"Header '{header_name}' not found. Adding it to the sheet.")
        next_column = len(headers) + 1
        sheet.update_cell(1, next_column, header_name)
        return next_column

def main():
    if not os.path.exists('qr_codes'):
        os.makedirs('qr_codes')

    records = exponential_backoff(fetch_all_data)
    print(f"Retrieved {len(records)} records from the sheet.")

    # Get correct column indices
    unique_id_col = get_column_index("Unique ID")
    sadhya_used_col = get_column_index("Sadhya Used")
    serial_code_col = get_column_index("Serial Code")

    n = int(input("Enter no. of records to process: "))
    processed_count = 0
    updates = []

    for idx, record in enumerate(records, start=2):  # start=2 because sheet is 1-indexed and we have a header row
        if processed_count >= n:
            break

        try:
            id_no = str(record.get('ID No.', ''))
            unique_id = record.get('Unique ID', '')

            if unique_id:
                print(f"Record with ID No. {id_no} already exists with Unique ID {unique_id}. Skipping.")
            elif id_no == '':
                print('Empty ID No. Skipping.')
            else:
                unique_id = str(uuid.uuid4())
                qr_filename = f"qr_codes/{id_no}.png"
                generate_qr_code(unique_id, qr_filename)
                serial_code = generate_serial_code()
                send_email(record['Email'], qr_filename, id_no, record['Name'], record['Phone Number'], record['Enrollment No.'], serial_code)

                updates.extend([
                    {'range': f'{gspread.utils.rowcol_to_a1(idx, unique_id_col)}', 'values': [[unique_id]]},
                    {'range': f'{gspread.utils.rowcol_to_a1(idx, sadhya_used_col)}', 'values': [['FALSE']]},
                    {'range': f'{gspread.utils.rowcol_to_a1(idx, serial_code_col)}', 'values': [[serial_code]]}
                ])

                processed_count += 1

        except Exception as e:
            print(f"Error processing record: {str(e)}")
            print("Traceback:")
            print(traceback.format_exc())
            continue

    if updates:
        exponential_backoff(lambda: batch_update(updates))

    print(f"Processed {processed_count} records.")

if __name__ == "__main__":
    main()
