#define REST_URL "http://127.0.0.1:%u/api/rest/rot13"
#define SERVER_PORT "8080"
#define MAC_ADDR_LEN 18             // "XX:XX:XX:XX:XX:XX\0"
#define MAX_BUFFER_SIZE 10          // Configurable length for the reading buffer
#define HIGH_VOLTAGE_THRESHOLD 3.8  // Voltage ratio threshold for events
#define KILO_BYTES 1024

#include <nng/http.h>
#include <nng/nng.h>

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// utility function
void if_fatal(const char *what, int rv)
{
    if (rv == 0) return;
    fprintf(stderr, "%s: %s\n", what, nng_strerror(rv));
    exit(EXIT_FAILURE);
}

// Structure for a single sensor reading
typedef struct {
    double v_ratio1;
    double v_ratio2;
    double v_ratio3;
    double temp1;
    double temp2;
    time_t timestamp;
} SensorReading;

// Structure for a threshold event
typedef struct Event {
    char mac_address[MAC_ADDR_LEN];
    char message[128];
    double value;
    time_t timestamp;
    struct Event *next;
} Event;

// Structure for managing a single device and its circular buffer
typedef struct DeviceData {
    char mac_address[MAC_ADDR_LEN];
    SensorReading readings[MAX_BUFFER_SIZE];
    int count;  // Current number of readings stored
    int head;   // Index of the oldest reading (circular buffer head)
    struct DeviceData *next;
} DeviceData;



// Global list heads
DeviceData *g_devices = NULL;
Event *g_events = NULL;

/// @brief Finds a DeviceData structure by MAC address.
/// @param mac The MAC address string.
/// @return Pointer to DeviceData if found, otherwise NULL.
DeviceData *find_device(const char *mac) {
    DeviceData *curr = g_devices;
    while (curr != NULL) {
        if (strcmp(curr->mac_address, mac) == 0) {
            return curr;
        }
        curr = curr->next;
    }
    return NULL;
}


/// @brief Adds a new reading to a device's circular buffer and checks for events.
/// @param device The device structure.
/// @param reading The new sensor reading.
void add_reading_and_check_events(DeviceData *device, const SensorReading *reading) {
    // 1. Add reading to circular buffer
    int idx = (device->head + device->count) % MAX_BUFFER_SIZE;
    device->readings[idx] = *reading;
    if (device->count < MAX_BUFFER_SIZE) {
        device->count++;
    } else {
        // If buffer is full, move the head to overwrite the oldest element
        device->head = (device->head + 1) % MAX_BUFFER_SIZE;
    }

    // 2. Check for threshold events (High Voltage Ratio 1)
    if (reading->v_ratio1 > HIGH_VOLTAGE_THRESHOLD) {
        Event *new_event = (Event *)malloc(sizeof(Event));
        if (new_event == NULL) {
            fprintf(stderr, "Error: Failed to allocate memory for event.\n");
            return;
        }

        // Populate event details
        strncpy(new_event->mac_address, device->mac_address, MAC_ADDR_LEN);
        snprintf(new_event->message, 128, "High Voltage Ratio (%.2f V) detected.", reading->v_ratio1);
        new_event->value = reading->v_ratio1;
        new_event->timestamp = reading->timestamp;
        new_event->next = NULL;

        // Add event to the global list (prepend for simplicity)
        // pthread_mutex_lock(&g_data_mutex);
        new_event->next = g_events;
        g_events = new_event;
        // pthread_mutex_unlock(&g_data_mutex);

        printf("EVENT: %s - %s\n", new_event->mac_address, new_event->message);
    }
}

/// @brief Utility to free the linked list of DeviceData.
void free_devices() {
    DeviceData *curr = g_devices;
    while (curr != NULL) {
        DeviceData *next = curr->next;
        free(curr);
        curr = next;
    }
    g_devices = NULL;
}

/// @brief Utility to free the linked list of Events.
void free_events() {
    Event *curr = g_events;
    while (curr != NULL) {
        Event *next = curr->next;
        free(curr);
        curr = next;
    }
    g_events = NULL;
}

/// @brief Handler for converting system state to application update packet
/// @param conn The connection object used by nng to send packet info
/// @param arg Extra parameters not yet used...
/// @param async I/O subsystem of nng to declare the state of the handler
void handle_pull(nng_http *conn, void *arg, nng_aio *async){
    size_t           sz;
    int              rv;
    void            *data;

    nng_http_get_body(conn, &data, &sz);

    nng_aio_finish(async, NNG_OK);
}

/// @brief Handler for converting device packets to sensor data structures
/// @param conn The connection object used by nng to collect packet info
/// @param arg Extra parameters not yet used...
/// @param async I/O subsystem of nng to declare the state of the handler
void handle_push(nng_http *conn, void *arg, nng_aio *async){
    size_t           sz;
    int              rv;
    void            *data;

    fprintf(stderr, "%s: %s\n", "Push Handler", nng_http_get_header(conn, "User-Agent"));
    nng_http_set_body(conn, "", 0);
    nng_http_set_status(conn, NNG_HTTP_STATUS_OK, nullptr);
    nng_aio_finish(async, NNG_OK);
}

int main(int argc, char **argv)
{
    nng_url *url;
    nng_http_server *server;
    nng_http_handler *push_callback, *pull_callback;

    if_fatal("cannot init NNG", nng_init(nullptr));

    if_fatal("url_parse", nng_url_parse(&url, "http://127.0.0.1:8888"));
    if_fatal("server_hold", nng_http_server_hold(&server, url));

    if_fatal("handler_alloc", nng_http_handler_alloc(&push_callback, "/submit", handle_push));
    nng_http_handler_set_method(push_callback, "POST");
    nng_http_handler_collect_body(push_callback, true, 1024 * 1024);
    if_fatal("server_add_handler (push)", nng_http_server_add_handler(server, push_callback));

    if_fatal("handler_alloc", nng_http_handler_alloc(&pull_callback, "/receive", handle_pull));
    nng_http_handler_set_method(pull_callback, "GET");
    if_fatal("server_add_handler (pull)", nng_http_server_add_handler(server, pull_callback));

    if_fatal("server_start", nng_http_server_start(server));

    for (;;) nng_msleep(1000);

    nng_url_free(url);
    nng_fini();
}