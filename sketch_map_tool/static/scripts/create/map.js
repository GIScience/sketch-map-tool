const map = new ol.Map({
    target: "map",
    view: new ol.View({
        center: ol.proj.fromLonLat([8.68, 49.41]),
        zoom: 15,
    }),
    layers: [
        new ol.layer.Tile({
            source: new ol.source.OSM(),
        }),
    ],
});

const printLayoutControl = new ol.control.PrintLayout({
    format: PAPER_FORMAT.A4,
    orientation: ORIENTATION.LANDSCAPE,
    margin: SKETCH_MAP_MARGINS.A4.landscape,
});
map.addControl(printLayoutControl);
