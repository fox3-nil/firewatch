#define INPROC_URL "inproc://rot13"
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

// This server acts as a proxy.  We take HTTP POST requests, convert them to
// REQ messages, and when the reply is received, send the reply back to
// the original HTTP client.
//
// The state flow looks like:
//
// 1. Receive HTTP request & headers
// 2. Receive HTTP request (POST) data
// 3. Send POST payload as REQ body
// 4. Receive REP reply (including payload)
// 5. Return REP message body to the HTTP server (which forwards to client)
// 6. Restart at step 1.
//
// The above flow is pretty linear, and so we use contexts (nng_ctx) to
// obtain parallelism.

typedef enum {
    SEND_REQ, // Sending REQ request
    RECV_REP, // Receiving REQ reply
} job_state;

typedef struct rest_job {
    nng_aio         *http_aio; // aio from HTTP we must reply to
    job_state        state;    // 0 = sending, 1 = receiving
    nng_msg         *msg;      // request message
    nng_aio         *aio;      // request flow
    nng_ctx          ctx;      // context on the request socket
    nng_http        *conn;
    struct rest_job *next; // next on the freelist
} rest_job;

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

nng_socket req_sock;

// We maintain a queue of free jobs.  This way we don't have to
// deallocate them from the callback; we just reuse them.
nng_mtx  *job_lock;
rest_job *job_freelist;

// Global list heads
DeviceData *g_devices = NULL;
Event *g_events = NULL;

// void inproc_server(void *arg);

static void rest_job_cb(void *arg);

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

static void rest_recycle_job(rest_job *job)
{
    if (job->msg != NULL) {
        nng_msg_free(job->msg);
        job->msg = NULL;
    }
    if (nng_ctx_id(job->ctx) != 0) {
        nng_ctx_close(job->ctx);
    }

    nng_mtx_lock(job_lock);
    job->next    = job_freelist;
    job_freelist = job;
    nng_mtx_unlock(job_lock);
}

static rest_job *rest_get_job(void) {
    rest_job *job;

    nng_mtx_lock(job_lock);
    if ((job = job_freelist) != NULL) {
        job_freelist = job->next;
        nng_mtx_unlock(job_lock);
        job->next = NULL;
        return (job);
    }
    nng_mtx_unlock(job_lock);
    if ((job = calloc(1, sizeof(*job))) == NULL) {
        return (NULL);
    }
    if (nng_aio_alloc(&job->aio, rest_job_cb, job) != 0) {
        free(job);
        return (NULL);
    }
    return (job);
    nng_http_hand
}

static void rest_http_fatal(rest_job *job, int rv) {
    nng_aio *aio = job->http_aio;

    // let the server give the details, we could have done more here
    // ourselves if we wanted a detailed message
    nng_aio_finish(aio, rv);
    rest_recycle_job(job);
}

static void rest_job_cb(void *arg) {
    rest_job *job = arg;
    nng_aio  *aio = job->aio;
    int       rv;

    switch (job->state) {
        case SEND_REQ:
            if ((rv = nng_aio_result(aio)) != 0) {
                rest_http_fatal(job, rv);
                return;
            }
            job->msg = NULL;
            // Message was sent, so now wait for the reply.
            nng_aio_set_msg(aio, NULL);
            job->state = RECV_REP;
            nng_ctx_recv(job->ctx, aio);
            break;
        case RECV_REP:
            if ((rv = nng_aio_result(aio)) != 0) {
                rest_http_fatal(job, rv);
                return;
            }
            job->msg = nng_aio_get_msg(aio);
            // We got a reply, so give it back to the server.
            rv = nng_http_copy_body(
                    job->conn, nng_msg_body(job->msg), nng_msg_len(job->msg));
            if (rv != 0) {
                rest_http_fatal(job, rv);
                return;
            }
            nng_http_set_status(job->conn, NNG_HTTP_STATUS_OK, NULL);
            nng_aio_finish(job->http_aio, 0);
            job->http_aio = NULL;
            // We are done with the job.
            rest_recycle_job(job);
            return;
        default:
            fatal("bad case", NNG_ESTATE);
            break;
    }
}

// Our rest server just takes the message body, creates a request ID
// for it, and sends it on.  This runs in raw mode, so
void rest_handle(nng_http *conn, void *arg, nng_aio *aio)
{
    struct rest_job *job;
    size_t           sz;
    int              rv;
    void            *data;

    if ((job = rest_get_job()) == NULL) {
        nng_aio_finish(aio, NNG_ENOMEM);
        return;
    }
    job->conn = conn;
    if (((rv = nng_ctx_open(&job->ctx, req_sock)) != 0)) {
        rest_recycle_job(job);
        nng_aio_finish(aio, rv);
        return;
    }

    nng_http_get_body(conn, &data, &sz);
    job->http_aio = aio;

    if ((rv = nng_msg_alloc(&job->msg, sz)) != 0) {
        rest_http_fatal(job, rv);
        return;
    }
    memcpy(nng_msg_body(job->msg), data, sz);
    nng_aio_set_msg(job->aio, job->msg);
    job->state = SEND_REQ;
    nng_ctx_send(job->ctx, job->aio);
}

void rest_start(uint16_t port)
{
    nng_http_server *server;
    nng_http_handler *handler;
    char rest_addr[128];
    nng_url *url;

    fatal("nng_mtx_alloc", nng_mtx_alloc(&job_lock));
    job_freelist = NULL;

    // Set up some strings, etc.  We use the port number
    // from the argument list.
    snprintf(rest_addr, sizeof(rest_addr), REST_URL, port);
    fatal("nng_url_parse", nng_url_parse(&url, rest_addr));

    // Create the REQ socket, and put it in raw mode, connected to
    // the remote REP server (our inproc server in this case).
    fatal("nng_req0_open", nng_req0_open(&req_sock));
    //fatal("nng_dial(" INPROC_URL ")", nng_dial(req_sock, INPROC_URL, NULL, NNG_FLAG_NONBLOCK));

    // Get a suitable HTTP server instance.  This creates one
    // if it doesn't already exist.
    fatal("nng_http_server_hold", nng_http_server_hold(&server, url));

    // Allocate the handler - we use a dynamic handler for REST
    // using the function "rest_handle" declared above.
    fatal("nng_http_handler_alloc", nng_http_handler_alloc(&handler, nng_url_path(url), rest_handle));

    nng_http_handler_set_method(handler, "POST");

    // We want to collect the body, and we (arbitrarily) limit this to
    // 128KB.  The default limit is 1MB.  You can explicitly collect
    // the data yourself with another HTTP read transaction by disabling
    // this, but that's a lot of work, especially if you want to handle
    // chunked transfers.
    nng_http_handler_collect_body(handler, true, 128 * KILO_BYTES);

    fatal("nng_http_handler_add_handler", nng_http_server_add_handler(server, handler));
    fatal("nng_http_server_start", nng_http_server_start(server));

    nng_url_free(url);
}

void handle_alpha(nng_http *connection, void *arg, nng_aio *async){}

int main(int argc, char **argv)
{
    int ret_val;
    // nng_thread *inproc_thr;
    uint16_t port = 0;
    if_fatal("cannot init NNG", nng_init(nullptr));

    if (getenv("PORT") != NULL) port = (uint16_t) atoi(getenv("PORT"));
    port = port ? port : 8888;

    nng_url *url;
    ret_val = nng_url_parse(&url, "http://127.0.0.1:8888/submit");
    if_fatal("", ret_val);

    nng_http_server *server;
    ret_val = nng_http_server_hold(&server, url);
    if_fatal("", ret_val);
    /// Critical Path
    nng_http_handler *handle;
    ret_val = nng_http_handler_alloc(&handle, "submit", handle_alpha);
    if_fatal("", ret_val);

    nng_http_handler_set_method(handle, "POST");
    nng_http_handler_collect_body(handle, true, 1024 * 1024);

    ret_val = nng_http_server_add_handler(server, handle);
    if_fatal("", ret_val);
    ret_val = nng_http_server_start(server);
    if_fatal("", ret_val);

    nng_fini();
}