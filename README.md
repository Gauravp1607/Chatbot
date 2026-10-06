# 🐄 LivestockAI — AI-Powered Animal Marketplace

LivestockAI is a full-stack web application designed to connect **livestock buyers and sellers through a centralized online marketplace**. The platform provides animal listings, advanced search and filtering, seller and buyer dashboards, secure communication, health records, reviews, ratings, and administrative management.

The project is built using **Python Flask, MySQL, HTML, CSS, and JavaScript**, with an architecture prepared for future AI integrations such as **animal disease detection using MobileNetV2** and an **AI livestock assistant using an LLM**.

## 🎯 Project Objective

The main objective of LivestockAI is to provide a digital platform where farmers, livestock sellers, and buyers can easily discover, list, compare, and communicate about animals.

The system aims to reduce the difficulty of finding suitable animals by providing:

- 🐄 Centralized livestock marketplace
- 🔎 Advanced animal search and filtering
- 👤 Buyer and seller accounts
- 💬 Buyer-seller communication
- ❤️ Favorites and wishlist
- ⭐ Reviews and ratings
- 🩺 Animal health and vaccination records
- 🔐 Secure authentication and role-based access
- 👨‍💼 Administrative management
- 🤖 AI-powered features planned for future development
- 📍 Location-based animal discovery planned for future development

## ✨ Key Features

### 👤 User Management

- User registration and login
- Role-based accounts:
  - Admin
  - Seller
  - Buyer
- Secure password hashing
- Session management
- Profile management
- Password reset functionality
- User status management
- Login history tracking

### 🐄 Livestock Marketplace

Users can browse and discover available animals through the marketplace.

Supported animal categories include:

- Cow
- Dog
- Cat
- Horse

Marketplace functionality includes:

- Animal listings
- Animal details
- Breed information
- Price information
- Age and gender
- Weight and health status
- Vaccination information
- Animal images
- Seller information
- Search and filtering
- Sorting
- Pagination
- Category-based browsing

### 🏪 Seller Features

Sellers can manage their livestock listings through their dashboard.

- Add new animals
- Upload animal images
- Edit listings
- Delete listings
- Manage inventory
- View inquiries
- Manage seller profile
- View seller information and ratings

### 🛒 Buyer Features

Buyers can search for animals based on their requirements.

- Browse animals
- Search and filter listings
- View detailed animal information
- Save animals to wishlist
- View buyer dashboard
- Track inquiries
- View purchase-related information

### 💬 Buyer-Seller Chat

LivestockAI includes a communication system that allows buyers and sellers to interact directly.

Features include:

- Conversation threads
- Text messaging
- Message history
- Read/unread status
- Message timestamps
- Chat notifications structure
- Attachment support structure

### ⭐ Reviews & Ratings

Buyers can provide feedback about sellers and animals.

- 1–5 star ratings
- Written reviews
- Edit reviews
- Delete reviews
- Seller rating calculation
- Review history

### 🩺 Animal Health Management

The platform maintains health-related information for animals.

The database supports:

- Vaccination history
- Disease history
- Health status
- Treatment records
- Disease severity
- Diagnosis dates
- Recovery information

## 🤖 AI Features

LivestockAI has been designed with an AI-ready architecture.

### 🧠 AI Disease Detection — Planned

A **MobileNetV2-based computer vision system** is planned to analyze uploaded animal images.

The planned system will provide:

- Animal image analysis
- Disease classification
- Prediction confidence score
- Treatment recommendations
- Disease detection history

The database already contains a dedicated structure for storing AI prediction records.

### 💬 AI Livestock Assistant — Planned

An AI assistant is planned to help users with livestock-related questions.

Potential capabilities include:

- Livestock health advice
- Breed recommendations
- Vaccination guidance
- Feeding recommendations
- Market price suggestions
- Natural-language interaction

The planned implementation uses an LLM API and stores conversation history for future analysis.

> **Note:** The AI integration is currently planned/under development and should not be considered fully implemented in the current version.

## 🛡️ Admin Panel

The platform includes an administrative management system.

Administrators can manage:

- Users
- Sellers
- Seller verification
- Reports and complaints
- Platform content
- User accounts
- Administrative activities
- Audit records

The system also maintains admin activity logs for tracking important administrative actions.

## 🗄️ Database Architecture

LivestockAI uses **MySQL 8.0** with an InnoDB storage engine.

The database is normalized to **Third Normal Form (3NF)** and contains:

- 16 tables
- 150+ columns
- 22 foreign keys
- 30+ indexes
- 27 relationships
- Multiple unique and check constraints

The database covers authentication, marketplace listings, health records, communication, reviews, notifications, AI logs, and administrative auditing.

## 🏗️ System Architecture

LivestockAI follows a **three-tier architecture**:

```text
┌─────────────────────────────────────────┐
│          PRESENTATION LAYER             │
│       HTML + CSS + JavaScript           │
│                                         │
│  Marketplace • Dashboards • Chat • UI   │
└───────────────────┬─────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│           APPLICATION LAYER             │
│              Python Flask               │
│                                         │
│ Authentication • Marketplace • Chat     │
│ Admin • Business Logic • Security       │
└───────────────────┬─────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│              DATA LAYER                 │
│                MySQL 8.0                │
│                                         │
│       16 Normalized Database Tables     │
└─────────────────────────────────────────┘
```

The architecture separates the presentation, application, and database layers, making the application easier to maintain and extend.

## 🛠️ Technology Stack

### Backend

- Python
- Flask
- PyMySQL
- Werkzeug
- Jinja2
- python-dotenv
- itsdangerous

### Frontend

- HTML5
- CSS3
- JavaScript
- Bootstrap 5
- Responsive Web Design

### Database

- MySQL 8.0+
- InnoDB
- UTF-8MB4
- 3NF normalized schema

### Planned AI/ML

- TensorFlow
- MobileNetV2
- Groq API
- OpenCV / Pillow
- Transformers

### Development Tools

- Git
- GitHub
- Visual Studio Code
- Pytest



## 📂 Project Structure

```text
LivestockAI/
│
├── app.py
├── config.py
├── models.py
├── requirements.txt
├── .env.example
│
├── database_final_production_schema.sql
├── apply_production_schema.py
├── apply_schema.py
│
├── test_app.py
├── test_query.py
├── inspect_db.py
├── inspect_routes.py
│
├── scripts/
│   ├── generate_reset_link.py
│   ├── reset_app_user.py
│   ├── import_database.py
│   ├── migrate_animals_schema.py
│   └── setup_db.ps1
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── animals.html
│   ├── animal_details.html
│   ├── login.html
│   ├── register.html
│   ├── profile.html
│   ├── seller_dashboard.html
│   ├── buyer_dashboard.html
│   ├── admin_dashboard.html
│   ├── wishlist.html
│   ├── disease_detection.html
│   └── ai_assistant.html
│
├── static/
│   ├── css/
│   ├── js/
│   ├── images/
│   └── uploads/
│
├── animals_dataset.csv
├── dataset_generation.py
└── import_csv.py
```

The project currently contains 27 HTML templates, 7 CSS files, 9 JavaScript files, and a production database schema.

## 🔐 Security

Security is an important part of the application architecture.

Implemented security features include:

- Password hashing using PBKDF2
- Session-based authentication
- Role-based access control
- Parameterized SQL queries
- Password reset tokens
- Login history
- File type validation
- User status management
- Administrative activity logging



## 📊 Project Status

| Component | Status |
|---|---|
| Database | ✅ 100% Complete |
| Backend | 🟡 60% Complete |
| Frontend | 🟡 60% Complete |
| Documentation | ✅ 100% Complete |
| AI Integration | 🔴 Planned |
| Testing | 🟡 Partial |
| Deployment | 🔴 Planned |

The project is currently in active development, with the database architecture completed and the core marketplace functionality implemented.

## 🚀 Future Roadmap

Planned improvements include:

- [ ] MobileNetV2 disease detection
- [ ] AI livestock assistant
- [ ] AI recommendation engine
- [ ] Google Maps integration
- [ ] Nearby animal search
- [ ] Payment gateway integration
- [ ] Real-time notifications
- [ ] Complete KYC verification
- [ ] Auction system
- [ ] Advanced analytics
- [ ] Mobile application
- [ ] Two-factor authentication
- [ ] Cloud deployment
- [ ] CI/CD pipeline
- [ ] Performance optimization

## 📈 Dataset

The project includes an animal image dataset containing five categories:

- Cat
- Cow
- Dog
- Goat
- Horse

The dataset contains multiple breeds and is intended to support future computer-vision and AI development.

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/LivestockAI.git
cd LivestockAI
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file using the provided `.env.example`:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_NAME=livestock_marketplace_prod
SECRET_KEY=your_secret_key
```

### 5. Setup MySQL Database

Create the database and apply:

```text
database_final_production_schema.sql
```

You can also use the provided database setup scripts.

### 6. Run the Application

```bash
python app.py
```

Open the application in your browser:

```text
http://127.0.0.1:5000
```

## 🧪 Testing

The project includes testing and inspection utilities for:

- Flask application testing
- Database queries
- Database structure
- Routes
- Environment configuration
- HTTP endpoints

Example:

```bash
python test_app.py
```

## 📚 Documentation

The project includes detailed documentation covering:

- Database architecture
- Database setup
- SQL queries
- Application architecture
- API routes
- Security
- Integration guidelines
- Migration procedures
- Future development roadmap

Major documentation files include:

```text
DATABASE_DESIGN_DOCUMENTATION.md
DATABASE_SETUP_GUIDE.md
DATABASE_DOCUMENTATION_INDEX.md
DATABASE_DELIVERABLES_SUMMARY.md
DATABASE_CLEANUP_GUIDE.md
PROJECT_COMPLETE_DOCUMENTATION.md
```

## 🎓 Project Highlights

LivestockAI demonstrates practical implementation of:

- Full-stack web development
- Python Flask development
- MySQL database design
- Database normalization
- Authentication and authorization
- Role-based access control
- Marketplace development
- Search and filtering
- Real-time communication architecture
- Health record management
- AI/ML integration planning
- Secure database operations
- Responsive frontend development

## 👨‍💻 Author

**Gaurav Panchal**

Master's in Data Science and Big Data Analytics

Interested in:

- Data Science
- Machine Learning
- Artificial Intelligence
- Python
- NLP
- Full-Stack AI Applications

---

⭐ If you find this project interesting, consider giving the repository a star!

**LivestockAI — Connecting Buyers, Sellers & Smart Animal Care through Technology.**
