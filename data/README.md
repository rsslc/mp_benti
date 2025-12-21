# Data Directory
This directory contains initial data and fixtures for the application.
## Structure
- **fixtures/** - JSON fixtures for loading initial data
  - `initial_data.json` - Complete data including users, categories, and products
  - `initial_data_no_users.json` - Data without users (for production)
- **initial_media/** - Initial category images
## Loading Data
Load complete data:
```bash
python manage.py loaddata data/fixtures/initial_data.json
```
Load data without users (recommended for production):
```bash
python manage.py loaddata data/fixtures/initial_data_no_users.json
```
