let pointBackgroundColor = []
let pointBorderColor = []
let graph = document.getElementById("graph").getContext('2d')
let chart = new Chart(graph, {
    type: "line",
    data: {
        labels: 'Data',
        datasets: [{
            label: "Values",
            backgroundColor: "rgba(0,0,0,1)",
            borderColor: "rgb(255, 52, 1)",
            pointBackgroundColor: pointBackgroundColor,
            pointBorderColor: pointBorderColor,
            data: 'Values'
        }]
    },
    spanGaps: true,
    options: {
        scales: {
            xAxes: {
                ticks: {
                    display: true,
                    autoskip: true,
                    maxTicksLimit: 6,
                    maxRotation: 0
                }
            }
        },
        responsive: true,
        spanGaps: true,
        elements: {
            point: {
                radius: 0
            }
        }
    }
})

function updateColors() {
    let flip = document.querySelector('#fs')
    if (flip.checked == true) {
        chart.options.elements.point.radius = 3
        chart.update()
    } else {
        chart.options.elements.point.radius = 0
        chart.update()
    }
}

function get_anomaly_index(data) {
    console.log("GETTING OUTLIER INDEXES")
    for (i = 0; i < data.length; i++) {
        if (data[i][2] == 1) {
            pointBackgroundColor.push('black');
            pointBorderColor.push('black');
        } else {
            pointBackgroundColor.push('transparent');
            pointBorderColor.push('transparent');
        }
    }
}

async function updateChart(new_data) {
    console.log("UPDATING CHART")
    let dates = []
    let values = []
    for (i = 0; i < new_data.length; i++) {
        dates.push(new_data[i][0])
        values.push(new_data[i][1])
    }
    chart.data.datasets[0].data = values
    chart.data.labels = dates
    chart.update()
    get_anomaly_index(new_data)
}

async function getGraphData() {
    console.log("GATHERING CHART DATA")
    let id = queryString.split("&");
    let calendar_range = document.getElementById('date_range').value
    let interpolation_rate = document.getElementById('slider').value
    const url = 'http://127.0.0.1:5000/datapoints?' + new URLSearchParams({
        id: id[0],
        choice: "all",
        range: calendar_range,
        int_rate: interpolation_rate,
        outliers: 'YES'
    })
    const response = await fetch(url)
        .then(function(response) {
            return response.json()
        })
        .then(function(complete_response) {
            let data = []
            for (i in complete_response.value) {
                let value_date = []
                value_date.push(complete_response.value[i][0].substring(5, 16))
                value_date.push(complete_response.value[i][1])
                value_date.push(complete_response.value[i][2])
                data.push(value_date)
            }
            updateChart(data)
        })
}

function updateInterpolation(val) {
    document.getElementById('points').value = val + ' points';
    getGraphData()
}

function initInterpolation() {
    document.getElementById('points').value = '600 points';
}

function getData() {
    let queryString = decodeURIComponent(window.location.search);
    queryString = queryString.substring(1);
    let id = queryString.split("&");
    let calendar_range = document.getElementById('date_range').value
    let interpolation_rate = document.getElementById('slider').value
    let radio_choice = document.querySelector('input[name="choice"]:checked').value
    fetch('http://127.0.0.1:5000/datapoints?' + new URLSearchParams({
            id: id[0],
            choice: radio_choice,
            range: calendar_range,
            int_rate: interpolation_rate,
            outliers: 'NO'
        }))
        .then(
            function(response) {
                return response.json()
            }
        )
        .then(
            function(complete_response) {
                console.log(complete_response)
                document.getElementById('value').innerHTML = complete_response.value
            }
        )
        .catch((err) => {
            console.log(err)
        })
}