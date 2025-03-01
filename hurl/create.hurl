# POST http://localhost:8081/en/create/results
POST https://test.sketch-map-tool.heigit.org/en/create/results
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

# GET http://localhost:8081/api/status/{{id}}/sketch-map
GET https://test.sketch-map-tool.heigit.org/api/status/{{id}}/sketch-map
[Options]
# retry for 1/2 minute
retry: 60
retry-interval: 500ms
HTTP 200
[Captures]
id: jsonpath "$.id"
[Asserts]
jsonpath "$.status" == "SUCCESS"

# GET http://localhost:8081/api/download/{{id}}/sketch-map
GET https://test.sketch-map-tool.heigit.org/api/download/{{id}}/sketch-map
[Options]
output: sketch-map.pdf
HTTP 200
