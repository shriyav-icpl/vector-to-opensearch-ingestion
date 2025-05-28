# File-Based Log Ingestion with Python, Vector and OpenSearch

This project demonstrates a simple pipeline for generating log files using a Python script, collecting these logs with Vector, and ingesting them into an OpenSearch cluster.

The `File_Approach` folder contains:
1.  `file_log_generator.py`: A Python script that continuously generates log messages to a file.
2.  `file.yml`: A Vector configuration file that tails the log file, attempts to parse its content, and sends it to OpenSearch.

## Prerequisites

1.  **Python 3**: To run the log generator script.
2.  **Vector**: Installed and available in your PATH. (Installation guide: [https://vector.dev/docs/setup/installation/](https://vector.dev/docs/setup/installation/))
3.  **OpenSearch Cluster**: An accessible OpenSearch (or Elasticsearch) cluster.
4.  **OpenSearch Credentials**: Username and password for your OpenSearch cluster.

## File Descriptions

### 1. `file_log_generator.py`

This Python script:
*   Sets up basic file logging to `file_log_generatorfile.log`.
*   Logs messages with the format: `YYYY-MM-DD HH:MM:SS,ms LEVEL Message`.
*   Continuously picks a random message from a predefined list (e.g., "User logged in", "Failed to load resource").
*   Logs the chosen message with `INFO` level.
*   Pauses for 3 seconds between log entries.

### 2. `file.yml` (Vector Configuration)

This configuration file defines how Vector processes the logs:

*   **`sources.file_source`**:
    *   **Type**: `file`
    *   **Include**: Monitors `file_log_generatorfile.log`.
    *   **`read_from`**: `beginning` - Reads the file from the start every time Vector launches (useful for testing, might be set to `end` for production).
    *   **`ignore_checkpoints`**: `true` - Vector won't save its read position (again, good for demos, not typically for production).

*   **`transforms.parse_and_add_timestamp`**:
    *   **Type**: `remap` (using Vector Remap Language - VRL).
    *   **Inputs**: Takes events from `file_source`.
    *   **Source (VRL Logic)**:
        ```vrl
        structured, err = parse_json(.message) # Attempts to parse the .message field as JSON
        if err == null {                     # If JSON parsing is successful:
          .timestamp = structured.timestamp #  - Sets .timestamp from the parsed JSON
          .level = structured.level         #  - Sets .level from the parsed JSON
          .message = structured.message     #  - Overwrites .message with the message from parsed JSON
        }
        .received_at = now()                 # Adds a new field 'received_at' with the current timestamp
        ```
        *   **Important Note**: The Python script *does not* output JSON formatted logs. It outputs plain text like `2023-10-27 10:00:00,123 INFO User logged in`. Therefore, the `parse_json(.message)` call will **fail**. The `if err == null` block will **not** be executed. The original `.message` (the plain text log line) will be preserved, and `timestamp` and `level` fields will *not* be extracted from the log content by this specific VRL logic. The primary effect of this transform will be adding the `.received_at` field.

*   **`sinks.opensearch_sink`**:
    *   **Type**: `elasticsearch` (compatible with OpenSearch).
    *   **Inputs**: Takes events from `parse_and_add_timestamp`.
    *   **Endpoints**: OpenSearch endpoint (configured via environment variable `OPENSEARCH_ENDPOINT`).
    *   **Auth**: Basic authentication using `OPENSEARCH_USER` and `OPENSEARCH_PASS` environment variables.
    *   **TLS**: `verify_certificate: false` - **WARNING**: This disables TLS certificate verification, making the connection insecure. Suitable for local development/testing only. **Do not use in production without proper certificate validation.**
    *   **Mode**: `bulk` for efficient batch writes.
    *   **Index**: Dynamically creates indices like `file_logs-YYYY.MM.DD`.
    *   **Compression**: `none`.
    *   **`suppress_type_name`**: `true` (required for newer Elasticsearch/OpenSearch versions).

## Setup and Running

1.  **Place Files**: Ensure both `file_log_generator.py` and `file.yml` are in the `File_Approach` directory.

2.  **Set Environment Variables**:
    Before running Vector, you need to set the following environment variables with your OpenSearch cluster details:
    ```bash
    export OPENSEARCH_ENDPOINT="your_opensearch_endpoint"      # Replace with your OpenSearch endpoint
    export OPENSEARCH_USER="your_username"                     # Replace with your OpenSearch username
    export OPENSEARCH_PASS="your_password"                     # Replace with your OpenSearch password
    ```

3.  **Run the Python Log Generator**:
    Open a terminal, navigate to the `File_Approach` directory, and run:
    ```bash
    python3 file_log_generator.py
    ```
    This script will start generating logs into `file_log_generatorfile.log` in the same directory. It will run indefinitely until you stop it (Ctrl+C).

4.  **Run Vector**:
    Open a *new* terminal, navigate to the `File_Approach` directory, and run Vector, pointing it to your configuration file:
    ```bash
    vector --config file.yml
    ```
    Vector will start, tail the `file_log_generatorfile.log`, process the log entries as per the configuration, and send them to your OpenSearch cluster.

## Expected Outcome

1.  The `file_log_generatorfile.log` will be created and populated with log lines like:
    `2023-10-27 12:34:56,789 INFO User logged in`

2.  In your OpenSearch cluster (e.g., via OpenSearch Dashboards or Kibana), you should see new indices being created daily with the pattern `file_logs-YYYY.MM.DD` (e.g., `file_logs-2023.10.27`).

3.  Documents within these indices will contain fields similar to this (exact fields might vary slightly based on default Vector enrichments):
    ```json
    {
      "message": "2023-10-27 12:34:56,789 INFO User logged in", // The raw log line from the file
      "received_at": "2023-10-27T12:35:00.123Z",               // Timestamp added by Vector when it processed the event
      "host": "your-machine-hostname",                         // Added by Vector
      "source_type": "file"                                    // Added by Vector
      // ... other potential metadata fields added by Vector
    }
    ```
## Customization and Improvements

*   **Production TLS**: For production, ensure `verify_certificate: true` (or remove the line, as true is often default) and configure `ca_file`, `crt_file`, `key_file` as needed for secure TLS communication with OpenSearch.
*   **Checkpointing**: For production, remove `ignore_checkpoints: true` from the file source to allow Vector to resume from where it left off after restarts.
*   **Error Handling**: Add more robust error handling in the VRL transform.

## Troubleshooting

*   **No logs in OpenSearch**:
    *   Check Vector's console output for errors (connection issues, authentication failures, mapping errors).
    *   Verify environment variables (`OPENSEARCH_ENDPOINT`, `OPENSEARCH_USER`, `OPENSEARCH_PASS`) are correctly set and exported in the shell where Vector is running.
    *   Ensure your OpenSearch cluster is reachable and the credentials are valid.
    *   Check if `file_log_generatorfile.log` is being written to by the Python script.