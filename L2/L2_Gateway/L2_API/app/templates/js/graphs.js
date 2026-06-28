window.addEventListener("DOMContentLoaded", () => {
    const element = document.getElementsByClassName("Graph")[0];
    element.innerHTML = '<canvas id="myChart"></canvas>';
    var ctx = document.getElementById('myChart').getContext('2d');

    console.log(measJS.map(measJS => measJS.raw_value));

    var myChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: measJS.map(measJS => measJS.timestamp),
            datasets: [{
                label: 'raw_value',
                data: measJS.map(measJS => measJS.raw_value),
                backgroundColor: [
                    'rgba(54, 162, 235, 0.2)',

                ],
                borderColor: [
                    'rgba(54, 162, 235, 1)',
                ],
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    suggestedMin: 0,
                    suggestedMax: Math.max(measJS.map(measJS => measJS.raw_value))
                }
            }
        }
    });


});