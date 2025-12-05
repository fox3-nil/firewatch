#define SERVER_PORT "80"
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
    struct {
        double v_ratio1; // Humd
        double v_ratio2; // CO2
        double v_ratio3; // METH
        double v_ratio4; // VOC
        double v_ratio5; // SMOKE
        double temp1; // Internal
        double temp2; // External
        time_t timestamp;
    } readings[MAX_BUFFER_SIZE];
    int count;  // Current number of readings stored
    int head;   // Index of the oldest reading (circular buffer head)
    struct DeviceData* next;
} DeviceData;

// Global list heads
DeviceData *device_list = NULL;
Event *event_list = NULL, *event_tail = NULL;


/// @brief Finds a DeviceData structure by MAC address.
/// @param mac The MAC address string.
/// @return Pointer to DeviceData if found, otherwise NULL.
DeviceData *find_device(const char *mac) {
    DeviceData *curr = device_list;
    // When the device list is empty
    if (curr == NULL) {
        device_list = malloc(sizeof (DeviceData));
        strcpy(device_list->mac_address, mac);
        return device_list;
    }
    // When the device is in a list
    while (curr->next != NULL) {
        if (strcmp(curr->next->mac_address, mac) == 0) return curr->next;
        curr = curr->next;
    }
    // When the device is not present
    curr->next = malloc(sizeof(DeviceData));
    strcpy(curr->next->mac_address, mac);
    return curr->next;
}

void create_event() {
    event_tail->next = malloc(sizeof(Event));
    event_tail = event_tail->next;
}

void threshold_events(const char *mac) {
    //if ()
}

/// @brief Handler for converting system state to application update packet
/// @param conn The connection object used by nng to send packet info
/// @param arg Extra parameters not yet used...
/// @param async I/O subsystem of nng to declare the state of the handler
void handle_push(nng_http *conn, void *arg, nng_aio *async){
    size_t           sz;
    int              rv;
    void            *data;
    DeviceData *device;

    char mac_address[MAC_ADDR_LEN];
    double itemp, etemp, humd, co2, meth, voc, smoke;

    const char *scan_format =
            "{ \"mac\": \"%17s\", \"itemp\": %f, \"etemp\": %f, \"humd\": %f, \"co2\": %f, \"meth\": %f, \"voc\": %f, \"smoke\": %f}";

    nng_http_get_body(conn, &data, &sz);
    int assignments = sscanf(data, scan_format, mac_address, &itemp, &etemp, &humd, &co2, &meth, &voc, &smoke);
    if (assignments != 8) fprintf(stderr, "Error: JSON parsing failed. Expected 8 assignments, got %d.\n", assignments);

    mac_address[MAC_ADDR_LEN - 1] = '\0';
    device = find_device(mac_address);

    int idx = (device->head + device->count) % MAX_BUFFER_SIZE;
    device->readings[idx].temp1 = itemp;
    device->readings[idx].temp2 = etemp;
    device->readings[idx].v_ratio1 = humd;
    device->readings[idx].v_ratio2 = co2;
    device->readings[idx].v_ratio3 = meth;
    device->readings[idx].v_ratio4 = voc;
    device->readings[idx].v_ratio5 = smoke;

    if (device->count < MAX_BUFFER_SIZE) device->count++;
    else device->head = (device->head + 1) % MAX_BUFFER_SIZE;
    // threshold_events(mac_address);

    nng_aio_finish(async, NNG_OK);
}

/// @brief Handler for converting device packets to sensor data structures
/// @param conn The connection object used by nng to collect packet info
/// @param arg Extra parameters not yet used...
/// @param async I/O subsystem of nng to declare the state of the handler
void handle_pull(nng_http *conn, void *arg, nng_aio *async){
    size_t           sz;
    int              rv;
    void            *data;

    fprintf(stdout, "%s: %s\n", "Push Handler", nng_http_get_header(conn, "User-Agent"));
    if_fatal("set_header", nng_http_set_header(conn, "Content-Type", "application/JSON"));
    const char *uri = nng_http_get_uri(conn);
    nng_url *url;
    nng_url_parse(&url, uri);
    char * body = malloc(300);
    if(device_list == NULL) strcpy(body, "{\"no_val\": 0}");
    else {
        const char *format = "{ \"mac\": \"%17s\", \"itemp\": %5.2f, \"etemp\": %5.2f, \"humd\": %3.2f, \"co2\": %3.2f, \"meth\": %3.2f, \"voc\": %3.2f, \"smoke\": %3.2f}\n";
        sprintf(body, format,
                device_list->readings[0].temp1,
                device_list->readings[0].temp2,
                device_list->readings[0].v_ratio1,
                device_list->readings[0].v_ratio2,
                device_list->readings[0].v_ratio3,
                device_list->readings[0].v_ratio4,
                device_list->readings[0].v_ratio5);
    }
    nng_http_set_body(conn, body, strlen(body));
    nng_http_set_status(conn, NNG_HTTP_STATUS_OK, NULL);
    nng_aio_finish(async, NNG_OK);
    free(body);
}

int main(int argc, char **argv)
{
    nng_url *url;
    nng_http_server *server;
    nng_http_handler *push_callback, *pull_callback, *index_callback, *dir_callback;

    if_fatal("cannot init NNG", nng_init(NULL));

    if_fatal("url_parse", nng_url_parse(&url, "http://172.31.7.192:80"));
    if_fatal("server_hold", nng_http_server_hold(&server, url));

    if_fatal("handler_alloc", nng_http_handler_alloc(&push_callback, "/submit", handle_push));
    nng_http_handler_set_method(push_callback, "POST");
    nng_http_handler_collect_body(push_callback, true, 1024 * 1024);
    if_fatal("server_add_handler (push)", nng_http_server_add_handler(server, push_callback));

    if_fatal("handler_alloc", nng_http_handler_alloc(&pull_callback, "/receive", handle_pull));
    nng_http_handler_set_method(pull_callback, "GET");
    nng_http_handler_set_tree(pull_callback);
    if_fatal("server_add_handler (pull)", nng_http_server_add_handler(server, pull_callback));

    if_fatal("handler_alloc", nng_http_handler_alloc_file(&index_callback, "/app/index.html", "./application/firewatch.html"));
    nng_http_handler_set_method(index_callback, "GET");
    if_fatal("server_add_handler (index)", nng_http_server_add_handler(server, index_callback));

    if_fatal("handler_alloc", nng_http_handler_alloc_directory(&dir_callback, "/app", "./application/"));
    nng_http_handler_set_method(dir_callback, "GET");
    if_fatal("server_add_handler (dir)", nng_http_server_add_handler(server, dir_callback));

    if_fatal("server_start", nng_http_server_start(server));

    for (;;) nng_msleep(10);

    nng_url_free(url);
    nng_fini();
}