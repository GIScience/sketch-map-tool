POST http://localhost:8081/en/digitize/results
[MultipartFormData]
file: file,sketch-map.png;
HTTP 302
[Captures]
# last part of URL is ID
id: header "Location" regex "([^/]+)/?$"

GET http://localhost:8081/api/status/{{id}}/vector-results
[Options]
# retry for 10 minute
retry: 600
retry-interval: 1s
# since uploaded sketch map is w/out markings
# the response 422 is expected
HTTP 422
[Asserts]
jsonpath "$.status" == "FAILURE"
jsonpath "$.errors[0]" contains "MarkingDetectionError"
