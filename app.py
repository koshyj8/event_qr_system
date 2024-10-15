from flask import Flask, request, jsonify, send_from_directory
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request 
import gspread
import os
import time

app = Flask(__name__)
from flask_cors import CORS
CORS(app)

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)

if creds and creds.expired and creds.refresh_token:
    creds.refresh(Request())

client = gspread.authorize(creds)

sheet = client.open('Onam Celebration Data').sheet1

@app.route('/')
def index():    
    return "Hello, World!"

@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('images', filename)

@app.route('/scanner.html')
def serve_scanner():
    return send_from_directory('', 'scanner.html')

@app.route('/scan', methods=['POST'])
def scan():
    try:
        data = request.json
        unique_id = data.get('unique_id')
        action = data.get('action') 
        service = data.get('service')
        
        if not unique_id or not action:
            return jsonify({'message': 'Invalid data', 'success': False}), 400
        
        headers = sheet.row_values(1)
        unique_id_col = headers.index("Unique ID") + 1
        sadhya_used_col = headers.index("Sadhya Used") + 1


        cell = sheet.find(unique_id)
        if not cell:
            return jsonify({'message': 'Participant not found', 'success': False}), 404
        row = cell.row
        name = sheet.cell(row, headers.index("Name") + 1).value
        if action == 'get_info':
            phone = sheet.cell(row, headers.index("Phone Number") + 1).value
            sadhya_used = sheet.cell(row, sadhya_used_col).value
            idnum = sheet.cell(row, headers.index("ID No.") + 1).value
            enrollmentno = sheet.cell(row, headers.index("Enrollment No.") + 1).value
            

            return jsonify({
                'success': True,
                'name': name,
                'phone_number': phone,
                'sadhya_used': sadhya_used,
                'id': idnum,
                'enrollment_no': enrollmentno,
                'row_no' : row - 1
                

            }), 200
        
        elif action == 'use_service':
            if not service:
                return jsonify({'message': 'Service not specified', 'success': False}), 400
            
            service_used = sheet.cell(row, sadhya_used_col).value
            
            if service_used == 'TRUE':
                response_message = f"Sadhya already availed for {name}!"
                success = False
            else:
                sheet.update_cell(row, sadhya_used_col, 'TRUE')
                response_message = f"Sadhya successfully availed for {name}!"
                success = True
                
            return jsonify({'message': response_message, 'success': success}), 200
        
        else:
            return jsonify({'message': 'Invalid action', 'success': False}), 400
        
    except gspread.exceptions.APIError as err:
        print(f"API error: {err}")
        return jsonify({'message': 'Google Sheets API error occurred while processing', 'success': False}), 500
    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({'message': 'Error occurred while processing', 'success': False}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
