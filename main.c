#include <libwebsockets.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>

// --- Data Structures for Storage ---

#define MAX_MAC_LEN 18 // XX:XX:XX:XX:XX:XX + '\0'

// Structure to hold sensor data
typedef struct sensor_data {
    char mac_address[MAX_MAC_LEN];
    float v1, v2, v3;
    float angle;
    float speed;
    float internal_temp;
    float external_temp;
    struct sensor_data *next;
} sensor_data_t;

// Global storage: simple linked list head
static sensor_data_t *global_data_store = NULL;
// Mutex to protect the shared global_data_store (crucial in LWS multi-threaded context)
static pthread_mutex_t *data_store_mutex = NULL;

// --- Helper Functions ---

// Function to validate MAC address format
static int validate_mac(const char *mac) {
    if (!mac || strlen(mac) != 17) {
        return 0;
    }
    // Basic check for XX:XX:XX:XX:XX:XX pattern (can be more rigorous)
    for (int i = 0; i < 17; i++) {
        if (i % 3 == 2) {
            if (mac[i] != ':') return 0;
        } else {
            if (!((mac[i] >= '0' && mac[i] <= '9') ||
                  (mac[i] >= 'a' && mac[i] <= 'f') ||
                  (mac[i] >= 'A' && mac[i] <= 'F'))) {
                return 0;
            }
        }
    }
    return 1;
}

// Finds data by MAC address (under the assumption that the mutex is already locked)
static sensor_data_t *find_data_by_mac_unlocked(const char *mac) {
    sensor_data_t *current = global_data_store;
    while (current) {
        if (strcmp(current->mac_address, mac) == 0) {
            return current;
        }
        current = current->next;
    }
    return NULL;
}

// Stores or updates sensor data (under the assumption that the mutex is already locked)
static void store_data_unlocked(sensor_data_t *new_data) {
    sensor_data_t *existing = find_data_by_mac_unlocked(new_data->mac_address);

    if (existing) {
        // Update existing entry
        existing->v1 = new_data->v1;
        existing->v2 = new_data->v2;
        existing->v3 = new_data->v3;
        existing->angle = new_data->angle;
        existing->speed = new_data->speed;
        existing->internal_temp = new_data->internal_temp;
        existing->external_temp = new_data->external_temp;
        free(new_data); // Free the temporary new_data struct
    } else {
        // New entry
        new_data->next = global_data_store;
        global_data_store = new_data;
    }
}

// Function to safely extract a float value using sscanf from a JSON field
static int extract_float(const char *json_data, const char *field, float *value) {
    const char *start = strstr(json_data, field);
    if (!start) return 0; // Field not found

    // Move past the field name, colon, and initial spaces/quotes
    start += strlen(field);
    while (*start && (*start == ' ' || *start == ':')) start++;

    // Attempt to read the float value
    if (sscanf(start, "%f", value) == 1) {
        return 1;
    }
    return 0; // Failed to parse float
}

// Function to safely extract a string value (MAC address)
static int extract_string(const char *json_data, const char *field, char *buffer, size_t buffer_len) {
    const char *start = strstr(json_data, field);
    if (!start) return 0; // Field not found

    // Move past the field name and colon
    start += strlen(field);
    while (*start && (*start == ' ' || *start == ':')) start++;

    // Find the opening quote
    const char *open_quote = strchr(start, '"');
    if (!open_quote) return 0;
    open_quote++;

    // Find the closing quote
    const char *close_quote = strchr(open_quote, '"');
    if (!close_quote) return 0;

    size_t len = close_quote - open_quote;
    if (len >= buffer_len) return 0; // Buffer overflow

    strncpy(buffer, open_quote, len);
    buffer[len] = '\0';
    return 1;
}

// --- Protocol Callback for /upload (Sensor Data Upload) ---

static int callback_upload(struct lws *wsi, enum lws_callback_reasons reason,
                           void *user, void *in, size_t len) {
    char *response_msg = NULL;

    switch (reason) {
        case LWS_CALLBACK_ESTABLISHED:
            lwsl_notice("Upload protocol established on /upload\n");
            break;

        case LWS_CALLBACK_RECEIVE: {
            lwsl_notice("Received %lu bytes on /upload.\n", (unsigned long)len);

            // 1. Allocate space for the new data structure
            sensor_data_t *new_data = (sensor_data_t *)calloc(1, sizeof(sensor_data_t));
            if (!new_data) {
                lwsl_err("Failed to allocate memory for sensor data.\n");
                response_msg = "{\"status\": \"error\", \"message\": \"Server allocation failed.\"}";
                goto send_response;
            }

            char mac_buf[MAX_MAC_LEN] = {0};

            // 2. Rudimentary JSON Parsing and Validation
            // Note: In a production app, use a dedicated JSON library (e.g., cJSON)
            if (!extract_string(in, "\"mac-address\"", mac_buf, sizeof(mac_buf)) ||
                !extract_float(in, "\"v1\"", &new_data->v1) ||
                !extract_float(in, "\"v2\"", &new_data->v2) ||
                !extract_float(in, "\"v3\"", &new_data->v3) ||
                !extract_float(in, "\"angle\"", &new_data->angle) ||
                !extract_float(in, "\"speed\"", &new_data->speed) ||
                !extract_float(in, "\"internal_temp\"", &new_data->internal_temp) ||
                !extract_float(in, "\"external_temp\"", &new_data->external_temp)) {

                lwsl_warn("Invalid JSON structure or missing fields received.\n");
                response_msg = "{\"status\": \"error\", \"message\": \"Invalid or incomplete JSON data.\"}";
                free(new_data);
                goto send_response;
            }

            // 3. MAC Address Validation
            if (!validate_mac(mac_buf)) {
                lwsl_warn("Invalid MAC address format received: %s\n", mac_buf);
                response_msg = "{\"status\": \"error\", \"message\": \"Invalid MAC address format.\"}";
                free(new_data);
                goto send_response;
            }

            // Copy validated MAC address to the struct
            strncpy(new_data->mac_address, mac_buf, MAX_MAC_LEN);

            // 4. Store Data (Thread-safe)
            pthread_mutex_lock(data_store_mutex);
            store_data_unlocked(new_data); // If updated, new_data is freed inside
            pthread_mutex_unlock(data_store_mutex);

            lwsl_notice("Data uploaded successfully for MAC: %s\n", new_data->mac_address);
            response_msg = "{\"status\": \"success\", \"message\": \"Sensor data stored/updated.\"}";

            break; // Data processing successful, don't jump to send_response yet
        }

        default:
            return 0;
    }

    // Common point to send response after processing
    if (response_msg) {
        send_response:
        // LWS requires a PADDING buffer for framing
        size_t msg_len = strlen(response_msg);
        unsigned char *p = (unsigned char *)malloc(LWS_PRE + msg_len + 1);
        if (!p) {
            lwsl_err("Failed to allocate response buffer.\n");
            return -1;
        }

        memcpy(p + LWS_PRE, response_msg, msg_len);
        p[LWS_PRE + msg_len] = '\0';

        // Send the message as text
        int written = lws_write(wsi, p + LWS_PRE, msg_len, LWS_WRITE_TEXT);
        free(p);

        if (written < (int)msg_len) {
            lwsl_err("Error writing response.\n");
        }
    }

    return 0;
}

// --- Protocol Callback for /data (Data Retrieval) ---

static int callback_data(struct lws *wsi, enum lws_callback_reasons reason,
                         void *user, void *in, size_t len) {

    switch (reason) {
        case LWS_CALLBACK_ESTABLISHED:
            lwsl_notice("Data protocol established on /data\n");
            break;

        case LWS_CALLBACK_RECEIVE: {
            // Received message should be the MAC address string
            char mac_buf[MAX_MAC_LEN] = {0};
            sensor_data_t *data = NULL;
            char *response_msg = NULL;

            // Ensure data is null-terminated and copy
            if (len >= MAX_MAC_LEN - 1) {
                response_msg = "{\"status\": \"error\", \"message\": \"MAC too long.\"}";
                goto send_response;
            }
            strncpy(mac_buf, (const char *)in, len);
            mac_buf[len] = '\0'; // Ensure termination

            lwsl_notice("Received request for MAC: %s\n", mac_buf);

            // 1. MAC Address Validation
            if (!validate_mac(mac_buf)) {
                lwsl_warn("Invalid MAC address format in request: %s\n", mac_buf);
                response_msg = "{\"status\": \"error\", \"message\": \"Invalid MAC address format.\"}";
                goto send_response;
            }

            // 2. Retrieve Data (Thread-safe)
            pthread_mutex_lock(data_store_mutex);
            data = find_data_by_mac_unlocked(mac_buf);
            pthread_mutex_unlock(data_store_mutex);

            // 3. Format Response
            if (data) {
                // Buffer for the JSON response
                char json_buffer[512];
                snprintf(json_buffer, sizeof(json_buffer),
                         "{"
                         "\"mac-address\": \"%s\","
                         "\"v1\": %.2f,"
                         "\"v2\": %.2f,"
                         "\"v3\": %.2f,"
                         "\"angle\": %.2f,"
                         "\"speed\": %.2f,"
                         "\"internal_temp\": %.2f,"
                         "\"external_temp\": %.2f"
                         "}",
                         data->mac_address, data->v1, data->v2, data->v3,
                         data->angle, data->speed, data->internal_temp, data->external_temp);
                response_msg = json_buffer;
            } else {
                lwsl_notice("Data not found for MAC: %s\n", mac_buf);
                response_msg = "{\"status\": \"not_found\", \"message\": \"No data found for this MAC address.\"}";
            }

            send_response:
            // Send the response
            size_t msg_len = strlen(response_msg);
            unsigned char *p = (unsigned char *)malloc(LWS_PRE + msg_len + 1);
            if (!p) {
                lwsl_err("Failed to allocate response buffer.\n");
                return -1;
            }

            memcpy(p + LWS_PRE, response_msg, msg_len);
            p[LWS_PRE + msg_len] = '\0';

            lws_write(wsi, p + LWS_PRE, msg_len, LWS_WRITE_TEXT);
            free(p);
            break;
        }

        default:
            return 0;
    }
    return 0;
}
enum path_identifiers {UPLOAD, DATA};
char *paths[] = {
        "/upload",
        "/data"
};
// --- Protocols Definition ---

static struct lws_protocols protocols[] = {
        {
                "http-only",         // Name
                lws_callback_http_dummy, // Callback
                      0,                   // Per-session data size
                         0,                   // Max frame size
                0, 0, 0        // LWS_RX_FLOW_CONTROL_START, uxsh_flags, peer_bfo_max, *rx_bind_if
        },
        {
                "sensor-upload-protocol", // Name
                callback_upload,          // Callback function
                      0,                        // Per-session data size
                         4096,                     // Max frame size
                0, 0,
                UPLOAD,                // Path mapping for this protocol
        },
        {
                "data-retrieval-protocol", // Name
                callback_data,             // Callback function
                      0,                         // Per-session data size
                         4096,                      // Max frame size
                0, 0,
                DATA,                   // Path mapping for this protocol
        },
        { NULL, NULL, 0, 0 } /* terminator */
};

// --- Main Server Setup ---

int main(int argc, const char **argv) {
    struct lws_context_creation_info info;
    struct lws_context *context;
    const char *p;
    int n = 0, logs = LLL_USER | LLL_ERR | LLL_WARN | LLL_NOTICE;
    int port = 7681;

    // Set up logging
    lws_set_log_level(logs, NULL);

    // Initialize global data store mutex
    if (pthread_mutex_init(data_store_mutex, NULL)) {
        lwsl_err("Failed to create mutex.\n");
        return 1;
    }

    // Zero-fill the context creation info struct
    memset(&info, 0, sizeof(info));
    info.port = port;
    info.protocols = protocols;
    info.gid = -1;
    info.uid = -1;
    info.options = LWS_SERVER_OPTION_ALLOW_HTTP_ON_HTTPS_LISTENER;

    // Create the context
    context = lws_create_context(&info);
    if (!context) {
        lwsl_err("lws init failed.\n");
        pthread_mutex_destroy(data_store_mutex);
        return 1;
    }

    lwsl_notice("Server started on port %d. Endpoints: /upload and /data\n", port);
    lwsl_notice("Press Ctrl-C to exit...\n");

    // Main event loop
    while (n >= 0) {
        n = lws_service(context, 50);
    }

    // Cleanup
    lwsl_notice("LWS cleanup...\n");
    lws_context_destroy(context);
    pthread_mutex_destroy(data_store_mutex);

    // Free the linked list memory
    sensor_data_t *current = global_data_store;
    sensor_data_t *next;
    while (current) {
        next = current->next;
        free(current);
        current = next;
    }

    return 0;
}