# HTTP Log Ingestion with Python, Vector and OpenSearch

This project demonstrates a pipeline for generating JSON log events using a Python script, sending them over HTTP to a Vector HTTP source, and ingesting them into an OpenSearch cluster.

The `HTTP_Approach` folder contains:
1.  `http_log_generator.py`: A Python script that continuously generates JSON log messages and POSTs them to Vector's HTTP endpoint.
2.  `http.yml`: A Vector configuration file that listens for HTTP requests, processes the incoming JSON logs, and sends them to OpenSearch.

## Prerequisites

1.  **Python 3**: To run the log generator script.
    *   **Python Libraries**: `requests`, `python-dotenv`. Install with:
        ```bash
        pip install requests python-dotenv
        ```
2.  **Vector**: Installed and available in your PATH. (Installation guide: [https://vector.dev/docs/setup/installation/](https://vector.dev/docs/setup/installation/))
3.  **OpenSearch Cluster**: An accessible OpenSearch (or Elasticsearch) cluster.
4.  **OpenSearch Credentials**: Username and password for your OpenSearch cluster.

## File Descriptions

### 1. `http_log_generator.py` (Python Script)

This Python script:
*   Optionally loads environment variables from a `.env` file (using `python-dotenv`).
*   Defines `VECTOR_HTTP_SOURCE` environment variable as the target URL for Vector's HTTP source.
*   Constructs log entries as Python dictionaries with `timestamp`, `level`, and `message` keys.
*   Serializes these dictionaries into JSON strings.
*   Continuously sends these JSON log entries via HTTP POST requests to the `VECTOR_HTTP_SOURCE` URL.
*   Includes basic error handling for the HTTP request.
*   Pauses for 3 seconds between sending log entries.

**Example JSON payload sent by the script:**
```json
{
    "timestamp": "2023-10-27T10:30:00Z",
    "level": "INFO",
    "message": "User logged in"
}
```

### 2. `http.yml` (Vector Configuration)

This configuration file defines how Vector processes the logs:

*   **`sources.http_source`**:
    *   **Type**: `http`
    *   **Address**: `${HTTP_ENDPOINT}` - The IP address and port Vector will listen on for incoming HTTP requests (e.g., `0.0.0.0:XXXX`). This is configured via an environment variable. Vector's HTTP source defaults to decoding incoming JSON payloads.

*   **`transforms.parse_and_add_timestamp`**:
    *   **Type**: `remap` (using Vector Remap Language - VRL).
    *   **Inputs**: Takes events from `http_source`.
    *   **Source (VRL Logic)**:
        ```vrl
        structured, err = parse_json(.message) # Attempts to parse the .message field of the event as JSON
        if err == null {                     # If JSON parsing is successful:
          .timestamp = structured.timestamp #  - Sets .timestamp from this (re-)parsed JSON
          .level = structured.level         #  - Sets .level from this (re-)parsed JSON
          .message = structured.message     #  - Overwrites .message from this (re-)parsed JSON
        }
        .received_at = now()                 # Adds a new field 'received_at' with current timestamp
        ```
        *   **Important Note on VRL Behavior**:
            *   The Python script sends a full JSON object (e.g., `{"timestamp": "...", "level": "...", "message": "..."}`).
            *   Vector's `http` source, by default (`decoding.codec = "json"`), will parse this incoming JSON. The fields from the Python script's JSON (`timestamp`, `level`, `message`) will already be top-level fields in the Vector event *before* this transform runs.
            *   So, when `parse_json(.message)` executes, `.message` will contain the string value like `"User logged in"`. Attempting to parse this string as JSON will **fail**.
            *   Consequently, the `if err == null` block will **not** be executed.
            *   The original `timestamp`, `level`, and `message` fields (that came directly from the Python script's JSON and were decoded by the `http` source) will be preserved.
            *   The primary effect of this specific transform, given the input, will be to add the `.received_at` field to the event.

*   **`sinks.opensearch_sink`**:
    *   **Type**: `elasticsearch` (compatible with OpenSearch).
    *   **Inputs**: Takes events from `parse_and_add_timestamp`.
    *   **Endpoints**: OpenSearch endpoint (configured via environment variable `OPENSEARCH_ENDPOINT`).
    *   **Auth**: Basic authentication using `OPENSEARCH_USER` and `OPENSEARCH_PASS` environment variables.
    *   **TLS**: `verify_certificate: false` - **WARNING**: This disables TLS certificate verification, making the connection insecure. Suitable for local development/testing only. **Do not use in production without proper certificate validation.**
    *   **Mode**: `bulk` for efficient batch writes.
    *   **Index**: Dynamically creates indices like `http_logs-YYYY.MM.DD`.
    *   **Compression**: `none`.
    *   **`suppress_type_name`**: `true` (required for newer Elasticsearch/OpenSearch versions).

## Setup and Running

1.  **Place Files**: Ensure `http_log_generator.py` (or your script name) and `http.yml` are in the same directory (e.g., `HTTP_Approach`).

2.  **Install Python Dependencies**:
    Navigate to the directory and run:
    ```bash
    pip install requests python-dotenv
    ```

3.  **Configure Environment Variables**:
    You need to set environment variables for both the Python script and Vector.

    *   **For the Python Script (`VECTOR_HTTP_SOURCE`)**:
        This is the full URL where Vector's HTTP source will be listening. You can set this directly in your shell or create a `.env` file in the same directory as `http_log_generator.py`:
        **`.env` file example:**
        ```
        VECTOR_HTTP_SOURCE="http://localhost:XXXX"
        ```
        If you use a `.env` file, the Python script will load it. Otherwise, export it:
        ```bash
        export VECTOR_HTTP_SOURCE="http://localhost:XXXX" # Adjust if Vector listens on a different host/port
        ```

    *   **For Vector (`vector.yaml`)**:
        Export these in the terminal where you will run Vector:
        ```bash
        # The address Vector listens on (must match the host/port in VECTOR_HTTP_SOURCE)
        export HTTP_ENDPOINT="0.0.0.0:XXXX" # Listens on port XXXX on all interfaces

        # OpenSearch Details
        export OPENSEARCH_ENDPOINT="your_opensearch_endpoint"      # Replace with your OpenSearch endpoint
        export OPENSEARCH_USER="your_username"                     # Replace with your OpenSearch username
        export OPENSEARCH_PASS="your_password"                     # Replace with your OpenSearch password
        ```
        **Important**: The host and port in `VECTOR_HTTP_SOURCE` (for Python) must be able to reach the address specified in `HTTP_ENDPOINT` (for Vector). If `HTTP_ENDPOINT` is `0.0.0.0:XXXX`, then `VECTOR_HTTP_SOURCE` can be `http://localhost:XXXX` or `http://<your_machine_ip>:XXXX`.

4.  **Run the Python Log Generator**:
    Open a *new* terminal, navigate to the project directory, and run:
    ```bash
    python3 http_log_generator.py
    ```
    This script will start sending JSON log data to Vector's HTTP endpoint. You should see output like:
    `Sent log: {'timestamp': '...', 'level': 'INFO', 'message': '...'} - Status: 200`

5.  **Run Vector**:
    Open a terminal, navigate to your project directory (e.g., `HTTP_Approach`), and run Vector, pointing it to your configuration file:
    ```bash
    vector --config http.yml
    ```
    Vector will start and listen for HTTP requests on the configured `HTTP_ENDPOINT`.

## Expected Outcome

1.  The Python script will print confirmation messages for successfully sent logs.
2.  Vector's console output will show logs related to receiving HTTP requests and sending data to OpenSearch.
3.  In your OpenSearch cluster (e.g., via OpenSearch Dashboards or Kibana), you should see new indices being created daily with the pattern `http_logs-YYYY.MM.DD` (e.g., `http_logs-2023.10.27`).
4.  Documents within these indices will contain fields directly from the JSON sent by Python, plus the `received_at` timestamp added by Vector:
    ```json
    {
      "timestamp": "2023-10-27T10:30:00Z",   // From the Python script's JSON
      "level": "INFO",                       // From the Python script's JSON
      "message": "User logged in",           // From the Python script's JSON
      "received_at": "2023-10-27T10:30:03.123Z", // Timestamp added by Vector transform
      "host": "your-machine-hostname",       // Added by Vector by default
      "source_type": "http"                // Added by Vector by default
      // ... other potential metadata fields added by Vector from HTTP request (e.g., headers, remote IP)
    }
    ```

## Customization and Improvements

*   **HTTP Source Authentication**: Secure Vector's HTTP endpoint using `auth` strategies if it's exposed to untrusted networks.
*   **Production TLS for OpenSearch**: For production, ensure `verify_certificate: true` (or remove the line) and configure `ca_file`, `crt_file`, `key_file` as needed for secure TLS communication with OpenSearch.
*   **Error Handling**: Implement more robust error handling in both the Python script and the Vector configuration (e.g., using dead_letter_queues in Vector).

## Troubleshooting

*   **Python script: "Connection refused" or timeout**:
    *   Ensure Python script is running *before* starting the Vector.
    *   Verify that `VECTOR_HTTP_SOURCE` in your Python environment/`.env` file correctly points to the `address` (and port) configured in `HTTP_ENDPOINT` in `http.yml`.
    *   Check for firewalls blocking the connection.
*   **Vector: "Address already in use"**:
    *   The port specified in `HTTP_ENDPOINT` is already being used by another application. Choose a different port.
*   **No logs in OpenSearch**:
    *   Check Vector's console output for errors (connection issues to OpenSearch, authentication failures, mapping errors).
    *   Verify `OPENSEARCH_ENDPOINT`, `OPENSEARCH_USER`, `OPENSEARCH_PASSWORD` environment variables for Vector.
    *   Ensure your OpenSearch cluster is reachable and credentials are valid.