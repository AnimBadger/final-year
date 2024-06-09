# English file to Twi AudioBook converter

This is a FastAPI application that allows users to upload English files (docx, doc, pdf, txt) and converts them to Twi. The application uses MongoDB as the backend for storing user data and converted files.


## Features

- **User Authentication:** Login and logout functionality.
- **File Upload:** Upload English files (docx, doc, pdf, txt).
- **File Conversion:** Convert uploaded files from English to Twi AudioBook.
- **File Storage:** Store converted files in MongoDB.
- **CORS Handling:** Configurable CORS for cross-origin requests.


## Prerequisites

- Docker
- Docker Compose
- API Keys:
  - **Ghana NLP:** [Sign up at Ghana NLP](https://translation.ghananlp.org/apis) to get your API key.
  - **Summarize AI:** [Sign up at AI21Studio](https://studio.ai21.com/account/api-key?source=docs) to get your API key.
  - **Rapid API Hub:** [Sign up at Rapid API](https://rapidapi.com/hub) to get your API key.

1. **Clone the Repository:**

    ```bash
    git clone https://github.com/AnimBadger/final-year.git
    cd final-year
    ```
   
2. **Environment Configuration:**

    Create a `.env` file in the root directory and add the following environment variables:

    ```env
    MONGO_URL=mongodb://mongo:27017
    JWT_SECRET=your_jwt_secret_key
    JWT_ALGORITHM=your_algorithm
    REFRESH_TOKEN_EXPIRE_DAYS=your_token_expire_days
    NLP_KEY=your_nlp_key
    SUMMARY_API=your_summary_api_key
    RAPID_API_KEY=your_rapid_api_key
    ```
   
3. **Docker Setup:**

    Ensure you have Docker and Docker Compose installed on your machine.

4. **Run Docker Compose:**

    ```bash
    docker-compose up --build
    ```

    This command will build the Docker images and start the containers.

## Usage

### Endpoints

- **Register User:**
    ```http
    POST /api/v1/auth/register
    ```
    ```json
    {
      "username": "username",
      "email": "your_email",
      "institution": "your_institution"
    }
    ```

- **Login:**

    ```http
    POST /api/v1/auth/login
    ```

    **Request Body:**

    ```json
    {
      "username": "your_username",
      "password": "your_password"
    }
    ```

- **Logout:**

    ```http
    POST /api/v1/auth/logout
    ```

- **Upload File:**

    ```http
    POST /api/v1/base/upload/{c_type}
    ```

    **Path Parameter:**

    - `c_type` (string): The type of conversion, summarize/full.

    **Form Data:**

    - `file` (file): The file to be uploaded.

- **List Audio Files:**

    ```http
    GET /api/v1/base/audio_files
    ```

- **Download Audio File:**

    ```http
    GET /audio_files/{file_id}/download
    ```
  **Path Parameter:**

  - `file_id` (string): id of file to be downloaded.
        

### Example Request

Using `curl` to upload a file:

```bash
curl -X POST "http://localhost:8000/api/v1/base/upload/{c_type}" \
    -H "Authorization: Bearer your_jwt_token" \
    -F "file=@/path/to/your/file.docx"
```