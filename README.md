# Opstream Project Setup Guide

## Prerequisites
- Python 3.11 or higher.
- Docker and Docker Compose.
- AWS account with SQS access.
- Slack workspace admin access.

## Installation

1. Clone the repository:

```bash
git clone https://github.com/Jose-Cabrera-FullStack/Opstream-challenge
```

2. Copy environment files:
```bash
cp .env.dev.example .env.dev
cp .env.prod.example .env.prod
```

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
SECRET_KEY=foo
DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1]
SQL_ENGINE=django.db.backends.postgresql
SQL_DATABASE=opstream_dev
SQL_USER=opstream
SQL_PASSWORD=opstream
SQL_HOST=db
SQL_PORT=5432
DATABASE=postgres

# SLACK
SLACK_CLIENT_ID=
SLACK_CLIENT_SECRET=
SLACK_SIGNING_SECRET=
SLACK_VERIFICATION=
SLACK_BOT_TOKEN=
SLACK_WORKSPACE_ACCESS_TOKEN=
SLACK_WORKSPACE_REFRESH_TOKEN=
SLACK_APP_LEVEL_TOKEN=

# SLACK
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=
AWS_SQS_QUEUE_NAME=
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


## Development Environment (Local) Commands

Inside the container, you can run the following commands (`docker-compose -it exec id-container bash`):

- `python manage.py makemigrations`: Create database migrations
- `python manage.py migrate`: Apply database migrations
- `python manage.py createsuperuser`: Create admin user
- `python manage.py test`: Run all tests
- `python manage.py test leak_shield`: Run leak_shield tests

## Production Environment Commands

`docker-compose -f docker-compose.prod.yml build`: Build the production image.

`docker-compose -f docker-compose.prod.yml up -d`: Run the production image.

`docker-compose -f docker-compose.prod.yml exec web python manage.py migrate`: Apply migrations.

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

## Architecture

The system consists of:

- Django web application.
- PostgreSQL database.
- AWS SQS queue for async processing.
- Slack event handlers.

## Roadmap

Follow the next steps:

[✓] 1. Open a free Slack account https://slack.com/pricing/free

[✓] 2. Use Slack events api https://api.slack.com/events-api to listen to messages

[✓] 3. Create a simple Data Loss Prevention tool that given a file, open its content and try to look for patterns (for example: a credit card number), using a list of regular expressions, make it possible to manage those patterns using django admin.

[✓] 4. Use django admin to also show messages that were caught by the DLP tool, show the message, its content and the pattern that caught it.

[✓] 5. Use the class above to create a container with distributed tasks to search for leaks in files and messages

[✓] 6. Write unit tests where consider appropriate.

[✓] 7. BONUS: add an action flow, so when DLP is giving a negative response, saying that the message contains a leak, the system should switch the message on slack with a message saying that the original message was blocked.

Pending items that could enhance the solution:
[✓] 1. Add Docker configuration for containerization.

[✓] 2. Add PostgreSQL database configuration.

[✓] 3. Add AWS SQS configuration and credentials setup.

[✓] 4. Add complete README with:

     - Project setup instructions.
     - How to run the tests.
     - How to deploy the system.

## Next Steps

1. Add support for more file types (currently only text files).
2. Implement proper error handling and logging
3. Add API documentation.
4. Add view to show messages caught by the DLP tool.
5. Add support for more patterns and regex rules.
6. Improve docker architecture.

## License

This project is licensed under the MIT License - see the LICENSE file for details.