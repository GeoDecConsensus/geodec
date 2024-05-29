document.addEventListener("DOMContentLoaded", function () {
    const map = L.map("map").setView([20, 0], 3)

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 18,
        attribution: "© OpenStreetMap",
    }).addTo(map)

    const markers = []
    const selectedCoordinates = []

    fetch("../rundata/servers.csv")
        .then((response) => response.text())
        .then((csvText) => {
            Papa.parse(csvText, {
                header: true,
                complete: function (results) {
                    results.data.forEach((place) => {
                        const marker = L.marker([
                            place.latitude,
                            place.longitude,
                        ])
                        marker
                            .setOpacity(0.5)
                            .addTo(map)
                            .on("click", function () {
                                const index = selectedCoordinates.findIndex(
                                    (coord) =>
                                        coord.latitude === place.latitude &&
                                        coord.longitude === place.longitude
                                )
                                if (index === -1) {
                                    selectedCoordinates.push(place)
                                    marker
                                        .bindTooltip(place.name, {
                                            permanent: true,
                                            direction: "right",
                                            className: "neon-text",
                                        })
                                        .openTooltip()
                                    marker.setOpacity(1)
                                } else {
                                    selectedCoordinates.splice(index, 1)
                                    marker.unbindTooltip()
                                    marker.setOpacity(0.5)
                                }
                            })
                        markers.push(marker)
                    })
                },
            })
        })

    window.downloadSelected = function () {
        const csv = Papa.unparse(selectedCoordinates)
        const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" })
        const link = document.createElement("a")

        if (link.download !== undefined) {
            const url = URL.createObjectURL(blob)
            link.setAttribute("href", url)
            link.setAttribute("download", "geo_input.csv")
            link.style.visibility = "hidden"
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
        }
    }
})
