# OpStream Project Setup Guide

## Prerequisites
- Python 3.11 or higher
- Docker and Docker Compose
- AWS account with SQS access
- Slack workspace admin access

## Installation

1. Clone the repository:

```bash
git clone
```

2. Copy environment files:
```bash
cp .env.dev.example .env.dev
cp .env.prod.example .env.prod
```

## Project Structure

The project contains the following configuration files:

- `config.yaml`: Contains the main configuration for the application.
- `docker-compose.yml`: Configuration for Docker Compose to set up the development environment.
- `.env`: Environment variables used by the application.
- `requirements.txt`: List of Python dependencies required for the project.

## Virtual Environment

Create a virtual environment and activate it:

```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# Unix/MacOS
source venv/bin/activate
```

## Install Dependencies

Install dependencies:

```bash
pip install -r requirements.txt
```

## Project Configuration

### Environment Variables

Create a .env.dev file with the following variables:

```bash
DEBUG=1
SECRET_KEY=your-secret-key
DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1]
```

## Run the Application

The project includes Docker support with:
```bash
# Build and start containers
docker-compose up --build

# Run in detached mode
docker-compose up -d

# Stop containers
docker-compose down
```

The application will be available at http://localhost:8000

The Docker configuration includes:

- `Dockerfile`: Python 3.11 slim image configuration
  - Creates a non-root user (appuser)
  - Sets up virtual environment
  - Installs dependencies
  - Configures security best practices
- `docker-compose.yaml`: Container orchestration
  - Exposes port 8000
  - Mounts volumes for development
  - Sets environment variables
  - Configures networking

## AWS Configuration

The project uses AWS SQS to send messages to Slack. To set up the AWS configuration:

1. Create an AWS account and navigate to the SQS service.
2. Create a new queue and note the queue URL.
3. Create an IAM user with programmatic access and attach the following policy:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "sqs:*",
            "Resource": "arn:aws:sqs:us-east-1:123456789012:my-queue"
        }
    ]
}
```

## Dependencies

The project uses the following main packages:

- Django 4.2.3
- Django REST Framework 3.14.0
- Python-dotenv 1.0.0
- Gunicorn 21.2.0
- Django CORS Headers 4.2.0

## Development local Commands

- `python manage.py makemigrations`: Create database migrations
- `python manage.py migrate`: Apply database migrations
- `python manage.py createsuperuser`: Create admin user
- `python manage.py test`: Run tests

## Development Production Commands

`docker-compose -f docker-compose.prod.yml build`: Build the production image
`docker-compose -f docker-compose.prod.yml up -d`: Run the production image
`docker-compose -f docker-compose.prod.yml exec web python manage.py migrate`: Apply migrations


## Architecture

The system consists of:

- Django web application
- PostgreSQL database
- AWS SQS queue for async processing
- Slack event handlers

## License

This project is licensed under the MIT License - see the LICENSE file for details.