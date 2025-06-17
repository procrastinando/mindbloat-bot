# MindBloat bot
Telegram bot to generate v2ray configs

## Prerequisites

*   **Docker and Docker Compose:** Ensure you have Docker and Docker Compose installed on your system.
    *   Docker: [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/)
*   **3XUI Instance:** A running instance of 3XUI accessible from where you run this bot.
*   **Telegram Bot Token:** A token for your Telegram bot, obtained from BotFather.

## Setup and Configuration

1.  **Create `docker-compose.yml`:**
    Create a file named `docker-compose.yml` in the same directory with the following content:

    ```yaml
    services:
    mindbloat:
        build:
            context: https://github.com/procrastinando/mindbloat-bot.git#main 
        image: procrastinando/mindbloat-bot:latest # image name
        container_name: mindbloat
        volumes:
            - mindbloat:/app
        environment:
            - PYTHONUNBUFFERED=1
            # Telegram Settings
            - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
            - TELEGRAM_BOT_NAME=${TELEGRAM_BOT_NAME}
            # Panel Details
            - PANEL_PROTOCOL=${PANEL_PROTOCOL}
            - PANEL_HOST=${PANEL_HOST}
            - PANEL_PORT=${PANEL_PORT}
            - WEB_BASE_PATH=${WEB_BASE_PATH}
            - PANEL_USERNAME=${PANEL_USERNAME}
            - PANEL_PASSWORD=${PANEL_PASSWORD}
            # Inbound & Server Details
            - INBOUND_REMARK=${INBOUND_REMARK}
            - SERVER_IP_OR_DOMAIN=${SERVER_IP_OR_DOMAIN}
            # New Client Settings
            - INITIAL_DATA_LIMIT_GB=${INITIAL_DATA_LIMIT_GB}
            - INITIAL_VALID_DAYS=${INITIAL_VALID_DAYS}
            - RENEWAL_DATA_GB=${RENEWAL_DATA_GB}
            - RENEWAL_DAYS=${RENEWAL_DAYS}
        env_file:
            .env
        restart: always
    ```