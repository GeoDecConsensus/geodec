document.addEventListener("DOMContentLoaded", function () {
    const map = L.map("map").setView([20, 0], 3)

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 18,
        attribution: "© OpenStreetMap",
    }).addTo(map)

    const markers = []
    const selectedCoordinates = []
    const selectedLocationsContainer =
        document.getElementById("selected-locations")

    fetch("./servers.csv")
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
                                    place.count = 1 // Initialize count
                                    place.stake = 1 // Initialize stake to 1
                                    selectedCoordinates.push(place)
                                    addLocationEntry(place)

                                    marker
                                        .bindTooltip(`${place.name}`, {
                                            permanent: true,
                                            direction: "right",
                                            className: "neon-text",
                                        })
                                        .openTooltip()
                                    marker.setOpacity(1)
                                } else {
                                    selectedCoordinates.splice(index, 1)
                                    removeLocationEntry(place)
                                    marker.unbindTooltip()
                                    marker.setOpacity(0.5)
                                }
                            })
                        markers.push(marker)
                    })
                },
            })
        })

    function addLocationEntry(place) {
        const entryDiv = document.createElement("div")
        entryDiv.className = "location-entry"
        entryDiv.dataset.latitude = place.latitude
        entryDiv.dataset.longitude = place.longitude

        const label = document.createElement("label")
        label.textContent = place.name

        const countInput = document.createElement("input")
        countInput.type = "number"
        countInput.value = place.count
        countInput.addEventListener("input", function () {
            place.count = parseInt(countInput.value, 10)
        })

        const stakeInput = document.createElement("input")
        stakeInput.type = "number"
        stakeInput.value = place.stake
        stakeInput.addEventListener("input", function () {
            place.stake = parseInt(stakeInput.value, 10)
        })

        entryDiv.appendChild(label)
        entryDiv.appendChild(countInput)
        entryDiv.appendChild(stakeInput)
        selectedLocationsContainer.appendChild(entryDiv)
    }

    function removeLocationEntry(place) {
        const entryDiv = selectedLocationsContainer.querySelector(
            `.location-entry[data-latitude='${place.latitude}'][data-longitude='${place.longitude}']`
        )
        if (entryDiv) {
            selectedLocationsContainer.removeChild(entryDiv)
        }
    }

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
    window.saveSelected = function () {
        fetch("/save-coordinates", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ coordinates: selectedCoordinates }),
        })
            .then((response) => response.text())
            .then((message) => alert(message))
            .catch((error) => console.error("Error:", error))
    }
})
