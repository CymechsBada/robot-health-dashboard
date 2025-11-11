
let chart = null;

document.addEventListener('DOMContentLoaded', function () {

  const sensorCanvas = document.getElementById('sensorChart');

  if (sensorCanvas) {

    const ctx = sensorCanvas.getContext('2d');



    // 초기 Chart 인스턴스 생성

    chart = new Chart(ctx, {

      type: 'line',

      data: { labels: [], datasets: [] },

      options: { responsive: true, scales: { x: { display: true }, y: { display: true } } }

    });



    // 필터 요소 이벤트 등록

    const filterElements = document.querySelectorAll('#sensorCheckboxes input[type="checkbox"], #command, #quickRange, #arm', '#startDate', '#endDate', '#stage');

    filterElements.forEach(el => {

      el.addEventListener('change', applyFilterFunction);

    });



    // 페이지 로드 시 초기 데이터 로드

    applyFilterFunction();

  } else {

    console.error("📌 sensorChart 요소를 찾을 수 없습니다.");

  }



  // pieChart는 필요할 때만 로드하는 방식 유지

  const pieCanvas = document.getElementById('errorLevelPieChart');

  if (pieCanvas) {

    console.warn("📌 pieChart 존재");

    fetch('/api/error-level-data')

      .then(response => response.json())

      .then(data => {

        if (!data || !Object.keys(data).length) {

          console.error("📌 error-level-data 응답 데이터 없음");

          return;

        }

        new Chart(pieCanvas.getContext('2d'), {

          type: 'pie',

          data: {

            labels: ['OK', 'CAUTION', 'WARNING', 'CRITICAL'],

            datasets: [{

              data: [data.OK, data.CAUTION, data.WARNING, data.CRITICAL],

              backgroundColor: ['#4CAF50', '#FFD700', '#FFA500', '#FF4C4C']

            }]

          },

          options: { responsive: true, plugins: { legend: { position: 'bottom' } } }

        });

      })

      .catch(err => console.error("📌 error-level-data fetch 에러:", err));

  }

});



function applyFilterFunction() {

  if (!chart) {

    console.warn("⚠️ Chart is not initialized yet. applyFilterFunction skipped.");

    return;

  }



  const startDate = document.getElementById('startDate')?.value;

  const endDate = document.getElementById('endDate')?.value;

  const command = document.getElementById('command')?.value;

  const stage = document.getElementById('stage')?.value;

  const arm = document.getElementById('arm')?.value;

  const selectedSensors = Array.from(document.querySelectorAll('#sensorCheckboxes input:checked')).map(cb => cb.value);



  fetch('/api/sensor-data', {

    method: 'POST',

    headers: {'Content-Type': 'application/json'},

    body: JSON.stringify({ startDate, endDate, command, stage, arm, sensors: selectedSensors })

  })

    .then(res => res.json())

    .then(data => updateChart(data));

}



function updateChart(data) {

  if (!chart) {

    console.error("❌ Chart 인스턴스가 존재하지 않아 updateChart를 실행할 수 없습니다.");

    return;

  }



  chart.data.labels = data.labels.map(label => label.split(' ')[0]);

  chart.data.datasets = data.datasets.map(sensor => {

    return {

      label: sensor.axis_name,
      name: sensor.name, 
      data: sensor.values,
      unit : sensor.unit,
      borderWidth: 2,
      borderColor: sensor.color,
      backgroundColor: sensor.color,
      fill: false,
      showLine: false,
      pointRadius: 1,

    };
  });

  // ✅ Y축 제목 설정 (첫 번째 센서 기준)
  const firstSensor = chart.data.datasets[0];
  const yAxisTitle = `${firstSensor.name}${firstSensor.unit ? ' (' + firstSensor.unit + ')' : ''}`;
  chart.options.scales.y.title = {
    display: true,
    text: yAxisTitle,
    font: { size: 14 }
  };

  chart.update();

}


