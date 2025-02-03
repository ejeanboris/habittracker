Understood. Since the Docker image is available on Docker Hub as `remi/habittracker`, you can set up the HabitTracker application without building the image locally. Here's the updated installation section, along with the `docker-compose.yml` and `.env` files:

---

## Installation

To set up the HabitTracker application using Docker, follow these steps:

1. **Clone the Repository**:
   ```bash
   git clone https://git.rehounou.ca/remi/habitTracker.git
   cd habitTracker
   ```

2. **Create a `.env` File**:
   - In the root directory of the project, create a file named `.env`.
   - Add the following content to the `.env` file:
     ```env
     NEXTCLOUD_URL=https://your-nextcloud-instance.com
    NEXTCLOUD_USERNAME=your_nextcloud_username
    NEXTCLOUD_PASSWORD=your_nextcloud_password

     ```

3. **Create a `docker-compose.yml` File**:
   - In the same directory, create a file named `docker-compose.yml`.
   - Add the following content:
     ```yaml
     version: '3.8'

    services:
    habittracker:
        image: remi/habittracker:latest
        ports:
        - "${STREAMLIT_PORT}:8501"
        volumes:
        - ./config:/app/config
        environment:
        - STREAMLIT_PORT=${STREAMLIT_PORT}
        - NEXTCLOUD_URL=${NEXTCLOUD_URL}
        - NEXTCLOUD_USERNAME=${NEXTCLOUD_USERNAME}
        - NEXTCLOUD_PASSWORD=${NEXTCLOUD_PASSWORD}
     ```

4. **Start the Application**:
   - Run the following command to start the application:
     ```bash
     docker-compose up -d
     ```

   The application will be accessible at `http://localhost:8501`.

---

**Notes**:

- The `docker-compose.yml` file defines a service named `habittracker` that uses the pre-built image `remi/habittracker:latest` from Docker Hub. It maps the port specified in the `.env` file to the container's port `8501` and mounts the `./config` directory to `/app/config` inside the container.

- The `.env` file allows you to specify environment variables, such as `STREAMLIT_PORT`, which can be used to configure the application's settings.

- Ensure that the `./config` directory exists in your project directory, as it will be used to store configuration files.

- If you need to set additional environment variables for your application, you can add them to the `.env` file and reference them in the `docker-compose.yml` file under the `environment` section.

By following these steps, you can set up and run the HabitTracker application using the pre-built Docker image from Docker Hub. 