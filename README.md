# Icarus - A Sanctuary for Human Creativity

A Flask web application for the Icarus platform, featuring user authentication, waitlist management, themed feeds, and a beautiful artistic design.

## Features

- **User Authentication**: Sign up, sign in, logout with session management
- **Multi-step Signup**: Beautiful two-step registration flow with theme selection
- **Waitlist System**: Early access signup with duplicate detection
- **Dashboard**: Protected user area with statistics
- **Themed Feeds**: Three theme options (Dark/Midnight, Light/Marble, Forest/Earth)
- **SQLite Database**: Simple, file-based database
- **Responsive Design**: Mobile-first approach with elegant styling

## Project Structure

```
icarus-flask/
├── app.py              # Main Flask application with all routes
├── config.py           # Configuration for dev/prod environments
├── requirements.txt    # Python dependencies
├── README.md           # This file
├── instance/           # SQLite database location
│   └── icarus.db       # Database file (auto-created)
├── static/
│   ├── icarus-logo.ico # Favicon
│   └── images/
│       ├── Gowy-icaro-prado.jpg
│       └── 37571d8f64ef1878e7e6439204eca3a7.jpg
└── templates/
    ├── base.html       # Base template with shared styles
    ├── index.html      # Landing page
    ├── signin.html     # Sign in page
    ├── signup.html     # Multi-step sign up
    ├── waitlist.html   # Waitlist signup
    ├── dashboard.html  # User dashboard
    ├── feed-forest.html # Feed with Forest/Earth theme
    ├── feed-dark.html  # Feed with Dark/Midnight theme
    ├── feed-light.html # Feed with Light/Marble theme
    ├── 404.html        # Not found error
    └── 500.html        # Server error
```

## Quick Start

### 1. Install Dependencies

```bash
cd icarus-flask
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python app.py
```

### 3. Open in Browser

Navigate to `http://localhost:5000`

## Database

The application uses SQLite with two models:

### User
| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| email | String(120) | Unique, indexed |
| password_hash | String(256) | Hashed password |
| name | String(100) | Optional |
| phone | String(20) | Optional |
| theme | String(20) | dark/light/earth |
| created_at | DateTime | Auto-set |
| is_active | Boolean | Default True |

### WaitlistEntry
| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| name | String(100) | Optional |
| email | String(120) | Unique, indexed |
| role | String(50) | Optional |
| source | String(50) | Signup source |
| created_at | DateTime | Auto-set |
| notified | Boolean | Default False |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/signup` | Create new user |
| POST | `/api/signin` | Authenticate user |
| POST | `/waitlist/submit` | Join waitlist |
| GET | `/api/waitlist` | List waitlist (auth required) |
| GET | `/api/user` | Current user info (auth required) |
| PUT | `/api/user/theme` | Update theme (auth required) |

## Page Routes

| Route | Description |
|-------|-------------|
| `/` | Landing page |
| `/signin` | Sign in form |
| `/signup` | Multi-step registration |
| `/waitlist` | Waitlist signup |
| `/dashboard` | User dashboard (protected) |
| `/feed` | Feed page with user's theme (protected) |
| `/feed/<theme>` | Feed page with specific theme (protected) |
| `/logout` | Sign out |

## Theme Options

Users can choose from three themes during signup or update later:

1. **Midnight (dark)** - Dark, refined aesthetic with black backgrounds
2. **Marble (light)** - Light, airy design with white/cream backgrounds  
3. **Forest (earth)** - Our signature look with deep forest green backgrounds

## Configuration

Environment variables for production:

```bash
export SECRET_KEY='your-secret-key-here'
export FLASK_ENV='production'
export DATABASE_URL='your-database-url'  # Optional, defaults to SQLite
```

## Development

The database is automatically created on first run. To reset:

```bash
rm instance/icarus.db
python app.py
```

## Testing the Application

1. Visit the landing page at `/`
2. Join the waitlist at `/waitlist`
3. Create an account at `/signup`
4. Sign in at `/signin`
5. View your dashboard at `/dashboard`
6. Browse the feed at `/feed`
7. Change settings at `/settings`

### Demo Account

A demo account is created automatically:
- **Email**: demo@icarus.art
- **Password**: demo1234

## Settings Page

The settings page (`/settings`) includes:

- **Profile**: Update name, username, email, bio
- **Appearance**: Switch between themes (Midnight, Marble, Forest)
- **Security**: Change password
- **Danger Zone**: Delete account

## License

All rights reserved.
