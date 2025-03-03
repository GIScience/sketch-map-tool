# POST http://localhost:8081/en/digitize/results
POST https://test.sketch-map-tool.heigit.org/en/digitize/results
[MultipartFormData]
file: file,sketch-map.png;
HTTP 302
[Captures]
# match UUID
id: header "Location" regex "/([0-9a-f-]{36})"

# GET http://localhost:8081/api/status/{{id}}/vector-results
GET https://test.sketch-map-tool.heigit.org/api/status/{{id}}/vector-results
[Options]
# retry for 10 minutes
retry: 600
retry-interval: 1s
# since uploaded sketch map is w/out markings
# the response 422 is expected
HTTP 422
[Asserts]
jsonpath "$.status" == "FAILURE"
jsonpath "$.errors[0]" contains "MarkingDetectionError"
