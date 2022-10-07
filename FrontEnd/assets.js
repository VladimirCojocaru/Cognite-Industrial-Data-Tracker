function loadAssets() {
    fetch('http://localhost:9090/backend')
        .then(function(response) {
            return response.json()
        })
        .then(function(complete_response) {
            let data = ''
            complete_response.map((values) => {
                console.log(values)
                data += `
                <div class="card">
                    <img src="../Images/asset.svg" alt="Avatar" style="width:100%">
                    <b>${values.name}</b>
                    <p><a style="font-size:20px" href=data.html?${values.id}&${values.name}>${values.id}</a><-tap to visualize data</p>
                    <p>Tracking data: ${values.used}</p>
                </div>
                `
                document.getElementById('cards').innerHTML = data
            })
        })
        .catch((err) => {
            console.log(err)
        })
}