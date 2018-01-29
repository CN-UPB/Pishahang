# [SONATA](http://www.sonata-nfv.eu)'s Gatekeeper Rate Limit micro-service
[![Build Status](http://jenkins.sonata-nfv.eu/buildStatus/icon?job=son-gkeeper)](http://jenkins.sonata-nfv.eu/job/son-gkeeper)


This is the folder of the Rate Limiter micro-service. 

The rate limiter is based on the [leaky bucket
algorithm](https://en.wikipedia.org/wiki/Leaky_bucket). Each client/limit has
an empty bucket assigned with a given capacity (according to a limit
definition). Each request goes into the bucket, that is leaking requests at a
given rate (again according to a limit definition). A client is allowed to
perform the request if there are remaining capacity in the bucket.

Example: Suppose that we have a limit that allows at maximum 6 requests per
minute. Then our bucket can hold at maximum 6 requests. However we’ll start 
draining our bucket after 60 seconds at a rate of 6reqs/60sec, that is 
removing one request from the bucket every 10 seconds.


# Rate Limit API
The rate limiter micro-service exposes a RESTful HTTP API that can perform basic
CRUD operations on rate limit definitions, and an endpoint to check resource
usage allowance.


## Create or update a rate limit definition
```
PUT /limits/{resource-limit-id}
```

A rate limit establishes how many requests in a time interval a client is
allowed to perform. For example, a client is allowed to perform at maximum 10
requests per hour.

This operation accepts the following parameters:

- **period** - Time sliding window (in seconds) for which the control of maximum
  number of requests is verified. (*required*)
- **limit** - Maximum number of requests that a client is allowed to perform in
  the specified period. (*required*)
- **description** - A human readable limit description. (*optional*)

### Sample request / response
The following request creates a limit, identified by
"check_account_balance_limit" where a client is allowed to perform a maximum of
10 requests per hour.

```json
PUT /limits/check_account_balance_limit
Content-Type: application/json
{
  "period": 3600,
  "limit": 10,
  "description": "Can check account balance 10 times / hour"
}

-- response
204 No Content
```

This operation can return the following HTTP status codes:
 - 204 No Content - The limit has been created or updated
 - 400 Bad Request - If the request is malformed, i.e., invalid values or missing parameters



## Delete resource limit
``` 
DELETE /limits/{resource-limit-id} 
```

This operation can return the following HTTP status codes:
 - 204 No Content - The limit was deleted 
 - 404 Not Found -  The specified resource limit does not exist.


## Retrieve existing resource limit definitions
``` 
GET /limits 
```
### Sample request / response
```json
GET /limits
-- response
200 OK
Content-Type: application/json
[
  { "id": "other_account_operations", "period": 60, "limit": 100 }, 
  { "id": "create_account", "period": 3600, "limit": 10, "description": "Can create 10 accounts / hour" },
  { "id": "default", "period": 1, "limit": 10, "description": "Global request rate policy is 10req/s"}
]
```


## Check limit
```
POST /check
```

This operation checks if a client is either allowed or not allowed to perform
the request according to the specified limit. Each call to this endpoint will
consume one request associated to the given client.

This operation accepts the following parameters:
 * **limit_id** - The limit identifier that should be applied. (*required*)
 * **client_id** - Any string that identifies the client. Cannot contain spaces. (*required*)


### Sample request / response
```json
POST /check
{
  "limit_id": "create_account",
  "client_id": "user_a"
}

-- response

200 Ok
{
  "allowed": true,
  "remaining": 10
}
```
Where the response body attributes:
 * allowed - If the client is allowed to perform the request. This can be either
   *true* or *false*.
 * remaining - Total number of available requests at the current time.

This operation can return the following HTTP status codes:
 - 200 Ok - Request was successfully processed. Client should inspect response
   body in order to check if client is allowed to perform the request.
 - 400 Bad Request - If the specified "limit_id" does not exist or the request
   is malformed




# Quick start
NOTE: In order to try this example you must have access to a redis instance. Set the
  `REDIS_URL` if necessary (defaults to "redis://127.0.0.1:6379") and `REDIS_PASSWORD` (not required)
  with the appropriate values.

Here's a quick start how to use the rate limiter. First start by creating a limit 
definition. In our example we're creating a limit that will allow one request 
each five seconds. 

```sh
curl -XPUT http://localhost:5000/limits/meaningfull_limit_id -d '{
  "period": 5,
  "limit": 1,
  "description": "Can check account balance 10 times / hour"
}'
```
Now that we have out limit definition, we can start sending requests. If you 
send a second request without waiting a few seconds, it will not be allowed.
```sh
curl -XPOST http://localhost:5000/check -d '{"limit_id": "meaningfull_limit_id", "client_id": "client1"}'
{"allowed":true,"remaining":0}

curl -XPOST http://localhost:5000/check -d '{"limit_id": "meaningfull_limit_id", "client_id": "client1"}'
{"allowed":false,"remaining":0}
```

Wait a few seconds and try again...
 
## License
The license of the SONATA Gatekeeper is Apache 2.0 (please see the
[license](https://github.com/sonata-nfv/son-editorgkeeper/blob/master/LICENSE)
file).


#### Feedback-Chanels

Please use the [GitHub issues](https://github.com/sonata-nfv/son-gkeeper/issues)
and the SONATA development mailing list `sonata-dev@lists.atosresearch.eu` for
feedback.

