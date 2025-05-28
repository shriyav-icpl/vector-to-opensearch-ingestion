# TCP Socket Log Ingestion with Python, Vector and OpenSearch

This project demonstrates a pipeline for generating JSON log events using a Python script, sending them over a TCP socket to a Vector `socket` source, and ingesting them into an OpenSearch cluster.

The `Socket_Approach` folder contains:
1.  `web_socket_log_generator.py`: A Python script that continuously generates JSON log messages and sends them over a TCP connection.
2.  `socket.yml`: A Vector configuration file that listens on a TCP socket, processes the incoming JSON logs, and sends them to OpenSearch.

## Prerequisites

1.  **Python 3**: To run the log generator script.
    *   **Python Libraries**: `python-dotenv`. Install with:
        ```bash
        pip install python-dotenv
        ```
2.  **Vector**: Installed and available in your PATH. (Installation guide: [https://vector.dev/docs/setup/installation/](https://vector.dev/docs/setup/installation/))
3.  **OpenSearch Cluster**: An accessible OpenSearch (or Elasticsearch) cluster.
4.  **OpenSearch Credentials**: Username and password for your OpenSearch cluster.

## File Descriptions

### 1. `web_socket_log_generator.py` (Python Script)

This Python script:
*   Optionally loads environment variables from a `.env` file for `HOST` and `PORT`.
*   Defines the target `HOST` and `PORT` for Vector's TCP socket listener.
*   Constructs log entries as Python dictionaries with `timestamp`, `level`, and `message` keys.
*   Serializes these dictionaries into JSON strings, appending a newline character (`\n`) to each, as Vector's `socket` source (with `codec: json`) typically expects line-delimited JSON.
*   Establishes a TCP connection to the specified `HOST` and `PORT`.
*   Continuously sends these JSON log entries over the TCP socket.
*   Includes basic connection status printing.
*   Pauses for 3 seconds between sending log entries.

**Example JSON string sent by the script (per line):**
```json
{"timestamp": "2023-10-27T10:30:00Z", "level": "INFO", "message": "User logged in"}\n
```

### 2. `socket.yml` (Vector Configuration)

This configuration file defines how Vector processes the logs:

*   **`sources.socket_source`**:
    *   **Type**: `socket`
    *   **Address**: `${SOCKET_ENDPOINT}` - The IP address and port Vector will listen on for incoming TCP connections (e.g., `0.0.0.0:XXXX`). This is configured via an environment variable.
    *   **Mode**: `tcp`
    *   **`encoding.codec`**: `json` - Instructs Vector to parse each line of incoming data on the TCP socket as a separate JSON object.

*   **`transforms.parse_and_add_timestamp`**:
    *   **Type**: `remap` (using Vector Remap Language - VRL).
    *   **Inputs**: Takes events from `socket_source`.
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
            *   The Python script sends a full JSON object per line (e.g., `{"timestamp": "...", "level": "...", "message": "..."}`).
            *   Vector's `socket` source, with `encoding.codec = "json"`, will parse each incoming line as a JSON object. The fields from the Python script's JSON (`timestamp`, `level`, `message`) will already be top-level fields in the Vector event *before* this transform runs.
            *   So, when `parse_json(.message)` executes, `.message` will contain the string value like `"User logged in"`. Attempting to parse this string as JSON will **fail**.
            *   Consequently, the `if err == null` block will **not** be executed.
            *   The original `timestamp`, `level`, and `message` fields (that came directly from the Python script's JSON and were decoded by the `socket` source) will be preserved.
            *   The primary effect of this specific transform, given the input, will be to add the `.received_at` field to the event.

*   **`sinks.opensearch_sink`**:
    *   **Type**: `elasticsearch` (compatible with OpenSearch).
    *   **Inputs**: Takes events from `parse_and_add_timestamp`.
    *   **Endpoints**: OpenSearch endpoint (configured via environment variable `OPENSEARCH_ENDPOINT`).
    *   **Auth**: Basic authentication using `OPENSEARCH_USER` and `OPENSEARCH_PASS` environment variables.
    *   **TLS**: `verify_certificate: false` - **WARNING**: This disables TLS certificate verification, making the connection insecure. Suitable for local development/testing only. **Do not use in production without proper certificate validation.**
    *   **Mode**: `bulk` for efficient batch writes.
    *   **Index**: Dynamically creates indices like `socket_logs-YYYY.MM.DD`.
    *   **Compression**: `none`.
    *   **`suppress_type_name`**: `true` (required for newer Elasticsearch/OpenSearch versions).

## Setup and Running

1.  **Place Files**: Ensure `web_socket_log_generator.py` and `socket.yml` are in the same directory (e.g., `Socket_Approach`).

2.  **Install Python Dependencies** (if using `.env`):
    Navigate to the directory and run:
    ```bash
    pip install python-dotenv
    ```

3.  **Configure Environment Variables**:
    You need to set environment variables for both the Python script and Vector.

    *   **For the Python Script (`HOST`, `PORT`)**:
        These define where the Python script will try to connect. You can set this directly in your shell or create a `.env` file in the same directory as `web_socket_log_generator.py`:
        **`.env` file example:**
        ```
        HOST="localhost"
        PORT="XXXX"
        ```
        If you use a `.env` file, the Python script will load it. Otherwise, export them:
        ```bash
        export HOST="localhost"   # Or the IP of the machine running Vector
        export PORT="XXXX"        # Must match the port Vector listens on
        ```

    *   **For Vector (`vector.yaml`)**:
        Export these in the terminal where you will run Vector:
        ```bash
        # The address Vector listens on (must match the HOST/PORT for Python script)
        export SOCKET_ENDPOINT="0.0.0.0:XXXX" # Listens on port XXXX on all interfaces

        # OpenSearch Details
        export OPENSEARCH_ENDPOINT="your_opensearch_endpoint"      # Replace with your OpenSearch endpoint
        export OPENSEARCH_USER="your_username"                     # Replace with your OpenSearch username
        export OPENSEARCH_PASS="your_password"                     # Replace with your OpenSearch password
        ```
        **Important**: The `HOST` and `PORT` for the Python script must be able to reach the address specified in `SOCKET_ENDPOINT` for Vector. If `SOCKET_ENDPOINT` is `0.0.0.0:XXXX`, then Python's `HOST` can be `localhost` (if on same machine) or the machine's IP, and `PORT` must be `XXXX`.

4.  **Run Vector**:
    Open a terminal, navigate to your project directory (e.g., `Socket_Approach`), and run Vector, pointing it to your configuration file:
    ```bash
    vector --config socket.yml
    ```
    Vector will start and listen for TCP connections on the configured `SOCKET_ENDPOINT`.

5.  **Run the Python Log Generator**:
    Open a *new* terminal, navigate to the project directory, and run:
    ```bash
    python3 web_socket_log_generator.py
    ```
    This script will attempt to connect to Vector and start sending JSON log data. You should see output like:
    `Connected to Vector TCP socket at localhost:XXXX`
    `Sent: {"timestamp": "...", "level": "INFO", "message": "..."}`

## Expected Outcome

1.  The Python script will print confirmation of connection and sent log messages.
2.  Vector's console output will show logs related to accepted TCP connections and sending data to OpenSearch.
3.  In your OpenSearch cluster (e.g., via OpenSearch Dashboards or Kibana), you should see new indices being created daily with the pattern `socket_logs-YYYY.MM.DD` (e.g., `socket_logs-2023.10.27`).
4.  Documents within these indices will contain fields directly from the JSON sent by Python, plus the `received_at` timestamp added by Vector:
    ```json
    {
      "timestamp": "2023-10-27T10:30:00Z",   // From the Python script's JSON
      "level": "INFO",                       // From the Python script's JSON
      "message": "User logged in",           // From the Python script's JSON
      "received_at": "2023-10-27T10:30:03.123Z", // Timestamp added by Vector transform
      "host": "your-machine-hostname",       // Added by Vector by default
      "source_type": "socket"                // Added by Vector by default
      // ... other potential metadata fields added by Vector (e.g., peer_ip from socket)
    }
    ```

## Customization and Improvements

*   **Production TLS for OpenSearch**: For production, ensure `verify_certificate: true` (or remove the line) and configure `ca_file`, `crt_file`, `key_file` as needed for secure TLS communication with OpenSearch.
*   **Error Handling**: Implement more robust error handling in the Vector configuration (e.g., using dead_letter_queues in Vector).
*   **Socket Source Security**: If exposing the TCP socket to a network, consider firewall rules or Vector's TLS options for the `socket` source if dealing with sensitive data over untrusted networks (though `socket` source TLS is more complex than `http` source).

## Troubleshooting

*   **Python script: "Connection refused" or timeout**:
    *   Ensure Vector is running *before* starting the Python script.
    *   Verify that `HOST` and `PORT` in your Python environment/`.env` file correctly point to the `address` (and port) configured in `SOCKET_ENDPOINT` in `vector.yaml`.
    *   Check for firewalls blocking the TCP connection on that port.
*   **Vector: "Address already in use"**:
    *   The port specified in `SOCKET_ENDPOINT` is already being used by another application. Choose a different port.
*   **No logs in OpenSearch**:
    *   Check Vector's console output for errors (connection issues to OpenSearch, authentication failures, mapping errors, JSON parsing errors from the socket if data is malformed).
    *   Verify `OPENSEARCH_ENDPOINT`, `OPENSEARCH_USER`, `OPENSEARCH_PASS` environment variables for Vector.
    *   Ensure your OpenSearch cluster is reachable and credentials are valid.