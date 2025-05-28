# Vector to OpenSearch Log Ingestion

This project demonstrates three distinct approaches for generating logs with Python, collecting them with Vector, and ingesting them into an OpenSearch cluster:

1.  **File-Based Ingestion**: Logs are written to a file, which Vector tails and send it to Opensearch.
2.  **HTTP-Based Ingestion**: Logs are sent as JSON payloads over HTTP to a Vector HTTP source and send it to Opensearch.
3.  **TCP Socket-Based Ingestion**: Logs are sent as JSON payloads over a TCP socket to a Vector socket source and send it to Opensearch.

Each approach is self-contained within its respective folder: `File_Approach`, `HTTP_Approach`, and `Socket_Approach`.

## Core Components

*   **Python 3**: Used for generating log messages.
*   **Vector**: A high-performance, end-to-end observability data pipeline. Used to collect, transform, and route logs. ([Installation Guide](https://vector.dev/docs/setup/installation/))
*   **OpenSearch**: A distributed, open-source search and analytics suite. Used as the destination for storing and analyzing logs.
## General Prerequisites

Before running any of the examples, ensure you have the following:

1.  **Python 3**: Installed and available in your PATH.
2.  **Vector**: Installed and available in your PATH.
3.  **OpenSearch Cluster**: An accessible OpenSearch cluster.
4.  **OpenSearch Credentials**: Username and password for your OpenSearch cluster. These will be set as environment variables:
    *   `OPENSEARCH_ENDPOINT`: The full URL of your OpenSearch endpoint (e.g., `https://your-opensearch-node:XXXX`).
    *   `OPENSEARCH_USER`: Your OpenSearch username.
    *   `OPENSEARCH_PASS`: Your OpenSearch password.

## Project Structure

```
.
├── File_Approach/
│   ├── file_log_generator.py       # Python script to generate logs to a file
│   └── file.yml                    # Vector configuration for file source
├── HTTP_Approach/
│   ├── http_log_generator.py       # Python script to send logs via HTTP
│   └── http.yml                    # Vector configuration for HTTP source
└── Socket_Approach/
    ├── web_socket_log_generator.py # Python script to send logs via TCP socket
    └── socket.yml                  # Vector configuration for socket source
```

---

## Overview of Approaches

1.  **File-Based Ingestion (`File_Approach/`)**:
    *   **Log Generation**: A Python script writes plain text logs to a local file (`file_log_generatorfile.log`).
    *   **Collection**: Vector tails this log file.
    *   **Ingestion**: Vector sends the log entries to OpenSearch.
    *   **Use Case**: Ideal for existing systems logging to files or when minimal application changes are desired.

2.  **HTTP-Based Ingestion (`HTTP_Approach/`)**:
    *   **Log Generation**: A Python script creates JSON log objects and POSTs them to an HTTP endpoint.
    *   **Collection**: Vector listens on this HTTP endpoint, receiving the JSON payloads.
    *   **Ingestion**: Vector forwards these structured logs to OpenSearch.
    *   **Use Case**: Common for microservices or applications that can easily send logs over HTTP(S); offers structured logging from the source.

3.  **TCP Socket-Based Ingestion (`Socket_Approach/`)**:
    *   **Log Generation**: A Python script creates JSON log objects and sends them as newline-delimited strings over a TCP socket.
    *   **Collection**: Vector listens on this TCP socket, parsing each line as a JSON object.
    *   **Ingestion**: Vector forwards these structured logs to OpenSearch.
    *   **Use Case**: Suitable for high-throughput scenarios where the overhead of HTTP is a concern; provides structured logging.

## General Guide to Run Any Approach

1.  **Clone/Download the Project**: Obtain all project files.
2.  **Navigate to an Approach Folder**:
    ```bash
    cd File_Approach  # or HTTP_Approach, or Socket_Approach
    ```
3.  **Set OpenSearch Environment Variables**: These are required for Vector to connect to your OpenSearch cluster. Set them in the terminal where you will run Vector:
    ```bash
    export OPENSEARCH_ENDPOINT="your_opensearch_endpoint_url" # Replace with your OpenSearch endpoint
    export OPENSEARCH_USER="your_username"                    # Replace with your OpenSearch username
    export OPENSEARCH_PASS="your_password"                    # Replace with your OpenSearch password
    ```
4.  **Set Approach-Specific Environment Variables**:
    *   **For `HTTP_Approach`**:
        *   Python script needs `VECTOR_HTTP_SOURCE` (e.g., `VECTOR_HTTP_SOURCE="http://localhost:XXXX"` or set in `.env`).
        *   Vector needs `HTTP_ENDPOINT` (e.g., `HTTP_ENDPOINT="0.0.0.0:XXXX"`).
    *   **For `Socket_Approach`**:
        *   Python script needs `HOST` and `PORT` (e.g., `HOST="localhost" PORT="XXXX"` or set in `.env`).
        *   Vector needs `SOCKET_ENDPOINT` (e.g., `export SOCKET_ENDPOINT="0.0.0.0:XXXX"`).
    *   **For `File_Approach`**: No additional source-specific environment variables are needed for the basic setup.

5.  **Install Python Dependencies** (if applicable for the chosen approach):
    *   For `HTTP_Approach`: `pip install requests python-dotenv`
    *   For `Socket_Approach`: `pip install python-dotenv`

6.  **Run Vector** (in one terminal, from the chosen approach's directory):
    ```bash
    # Example for File_Approach
    vector --config file.yml

    # Example for HTTP_Approach
    vector --config http.yml

    # Example for Socket_Approach
    vector --config socket.yml
    ```
    Vector will start and (for HTTP/Socket) listen for incoming logs or (for File) start tailing the log file.

7.  **Run the Python Log Generator** (in a *new* terminal, from the chosen approach's directory):
    ```bash
    # Example for File_Approach
    python3 file_log_generator.py

    # Example for HTTP_Approach
    python3 http_log_generator.py

    # Example for Socket_Approach
    python3 web_socket_log_generator.py
    ```
    The script will start generating and sending logs.

8.  **Verify in OpenSearch**:
    *   Check your OpenSearch Dashboards (or query via API).
    *   New indices (e.g., `file_logs-YYYY.MM.DD`, `http_logs-YYYY.MM.DD`, `socket_logs-YYYY.MM.DD`) should be created.
    *   Documents within these indices should contain the log data.

## Conclusion

This project provides a practical starting point for understanding and implementing different log ingestion strategies using Python, Vector, and OpenSearch.
Each approach has its trade-offs:

*   **File-based** is excellent for integrating with systems already producing file logs.
*   **HTTP-based** is versatile and standard for application-level logging, especially with JSON.
*   **Socket-based** offers a potentially lower-overhead method for high-volume, structured log streams.

Explore each approach to determine which best fits your specific logging requirements and infrastructure.
