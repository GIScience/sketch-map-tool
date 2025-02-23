POST {{url}}/en/create/results
[FormParams]
format: A4
orientation: landscape
bbox: [964876.9155641538,6343759.995301168,967132.6040690138,6345647.98995813]
bboxWGS84: [8.667636805453803,49.40439835925838,8.687900000055087,49.41543335522428]
size: {"width":1716,"height":1436}
scale: 8421.817229430539
layer: OSM
[Options]
HTTP 302
[Captures]
# match UUID
id: header "Location" regex "/([0-9a-f-]{36})/"

GET {{url}}/api/status/{{id}}/sketch-map
[Options]
# retry for 1/2 minute
retry: 60
retry-interval: 500ms
HTTP 200
[Captures]
id: jsonpath "$.id"
[Asserts]
jsonpath "$.status" == "SUCCESS"

GET {{url}}/api/download/{{id}}/sketch-map
[Options]
output: sketch-map.pdf
HTTP 200
