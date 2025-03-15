# Workify

A platform that connects local service providers with customers, powered by LastAppStanding.

## Overview

Workify is designed to make it easier for people to find and hire local service providers for various tasks, and for skilled professionals to find work opportunities in their area. The platform caters to two types of users:

1. **Job Seekers**: Professionals looking for work opportunities in their area
2. **Job Posters**: Customers looking to hire skilled professionals for specific tasks

## Features

### For Job Seekers

- Create a professional profile showcasing skills and experience
- Browse local job opportunities based on location and skills
- Apply to jobs with a streamlined application process
- Track application status in real-time
- Communicate directly with potential employers
- Showcase portfolio of past work
- Receive reviews and ratings from employers
- Find nearby job posters (Premium feature)

### For Job Posters

- Post detailed job listings with requirements and budget
- Browse profiles of local professionals
- Review applications and credentials
- Communicate directly with applicants
- Leave reviews for completed work
- Find nearby job seekers (Premium feature)

## Technical Stack

- **Frontend**: Streamlit
- **Backend**: Python
- **Database**: SQLite
- **Authentication**: Google OAuth
- **Geolocation**: Integrates with location services
- **Maps**: Leaflet for interactive maps

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/workify.git
   cd workify
   ```

2. Create a virtual environment:
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up the environment variables in .env file:
   ```bash
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   REDIRECT_URI=http://localhost:8501/
   ```

5. Initialize the database:
   ```bash
   python init_db.py
   ```

6. Run the application:
   ```bash
   streamlit run app.py
   ```

## Usage

### Account Creation

Users can sign up using their Google account and select their role (Job Seeker or Job Poster) during the onboarding process.

### Job Seeker Workflow

1. Create a profile with skills, experience, and location
2. Browse available jobs in the area
3. Apply to relevant jobs
4. Communicate with potential employers
5. Complete jobs and receive ratings

### Job Poster Workflow

1. Create a profile with contact information
2. Post a job with detailed requirements
3. Review applications from professionals
4. Select and communicate with candidates
5. Complete the hiring process and leave reviews

## Premium Features

Workify offers a premium subscription that unlocks additional features:

- For Job Seekers: Priority application visibility, advanced search filters, and more
- For Job Posters: Featured job listings, advanced candidate filtering, and more
- For Both: Access to the nearby users feature to find local opportunities

## Development

### Project Structure

- `app.py`: Main application entry point
- `pages/`: Different pages of the application
- `utils/`: Utility functions and modules
- `components/`: Reusable UI components
- `static/`: Static assets like images and CSS
- `schema.sql`: Database schema definition

## License

[Insert License Information Here]

## Contact

For any questions or inquiries, please contact LastAppStanding at [your-email@example.com].

---

&copy; 2024 LastAppStanding. All rights reserved. 