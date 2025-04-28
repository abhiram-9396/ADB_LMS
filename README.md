# 📚 Library Management System (LMS)

A real-time web-based **Library Management System** built with **Flask** and **MongoDB**. Designed to streamline book check-ins/check-outs, payment processing, reservations, and personalized learning history tracking for a seamless user experience.

## 🚀 Features

- **Check-In / Check-Out Books:** Borrow and return books with real-time status updates.
- **Due Payments Management:** Process overdue payment calculations and clear balances securely.
- **Request & Reserve Titles:** Reserve books ahead of time to ensure availability.
- **Advanced Filtering:** Search and filter books by **ISBN**, **location**, and **genre**.
- **User Profiles:** Track learning history and view personalized book recommendations.
- **Real-Time Updates:** Seamless UI and database synchronization.

## 🛠️ Built With

- **Flask** – Lightweight Python web framework
- **MongoDB** – NoSQL database for storing books, transactions, and user data
- **HTML5 & CSS3** – Frontend structure and design
- **Bootstrap** – Responsive design and styling
- **JavaScript** – For form validations and in app functionality
- **PyMongo** – MongoDB integration with Flask

## 🗂️ Project Presentation

To explore the **database architecture**, **features breakdown**, and **project workflow**, view the full project presentation:

👉 [Project Presentation – Database Architecture & Details](https://docs.google.com/presentation/d/1Hh-6hazY5oOWqBIw_BwjFwTzoJ4f5WDrfeP12d-eMHE/edit?usp=sharing)

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/abhiram-9396/ADB_LMS.git
   cd ADB_LMS
   ```

2. **Create and activate a virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   - Create a `.env` file
   - Add your MongoDB connection string:
     ```
     MONGO_URI=your-mongodb-connection-string
     SECRET_KEY=your-secret-key
     ```

5. **Run the application:**
   ```bash
   flask run
   ```

6. **Access the app:**
   - Open `http://127.0.0.1:5000` in your browser.

## 🔒 Security Measures

- CSRF Protection on all forms using **Flask-WTF**.
- Secure MongoDB queries to prevent injection attacks.
- Environment variables used to store sensitive configurations.

## ✨ Future Enhancements

- Admin dashboard for book and user management.
- Email notifications for due dates and reservations.
- Integration with external ISBN databases (e.g., Google Books API).
- Export user borrowing history as a report.

## 🙌 Acknowledgments

- Thanks to the Flask and MongoDB communities for excellent documentation and support.
- Project inspired by the need to make book borrowing and tracking effortless in educational institutions.

---

**Note:** This LMS project was created for educational purposes and personal development.
