# Event QR System

This project is a comprehensive solution for managing event participation using QR codes. It's designed to streamline the process of participant check-ins, service availing, and coupon distribution. Built with flexibility and scalability in mind, this system is ideal for any event where tracking attendance and managing participant services are critical.

## Features

- **QR Code Scanning:** Efficiently scan QR codes to identify participants and manage their services.
- **Participant Management:** Retrieve participant information and update service usage in real-time.
- **Service Availing:** Participants can use their QR codes to avail services like meals or event perks.
- **Responsive Design:** User interface is optimized for both desktop and mobile devices.

## Technology Stack

- **Frontend:** HTML, CSS, JavaScript
- **Backend:** Flask (Python)
- **Database:** Google Sheets (gspread)
- **QR Code Generation:** `qrcode` library for Python
- **Email Integration:** Python's `smtplib` for sending customized emails

## Setup Instructions

1. **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/event-qr-system.git
    cd event-qr-system
    ```

2. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3. **Configure environment variables:**
    - Create a `.env` file in the root directory and add your configuration settings (e.g., email server details, secret keys).

4. **Run the application:**
    ```bash
    flask run
    ```

5. **Access the application:**
    - Open your browser and navigate to `http://127.0.0.1:5000` to use the system.

## Usage

- **Admin Dashboard:** Access the dashboard to monitor participant check-ins, view statistics, and manage services.
- **Participant Interface:** Participants can scan their QR codes on the day of the event to check-in and avail of services.

## Contributing

Contributions are welcome! Feel free to submit a pull request or open an issue to discuss your ideas.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

