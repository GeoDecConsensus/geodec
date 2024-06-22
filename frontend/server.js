const express = require("express")
const bodyParser = require("body-parser")
const fs = require("fs")
const path = require("path")
const Papa = require("papaparse")

const app = express()
const PORT = 3000

app.use(bodyParser.json())

app.use(express.static("public")) // Serve static files from 'public' directory

app.post("/save-coordinates", (req, res) => {
    const selectedCoordinates = req.body.coordinates

    // Convert JSON data to CSV
    const csv = Papa.unparse(selectedCoordinates)

    // Write CSV to file
    const filePath = path.join(__dirname, "..", "rundata", "geo_input.csv")
    fs.writeFile(filePath, csv, (err) => {
        if (err) {
            console.error("Error writing file:", err)
            return res.status(500).send("Error saving file")
        }
        res.send("File saved successfully")
    })
})

app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`)
})
