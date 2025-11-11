document.addEventListener('DOMContentLoaded', () => {
  const chartCanvas = document.getElementById('sensorChart').getContext('2d');
  let chart;

  const levelColorMap = {
    'OK': '#4CAF50',
    'WARNING': '#FFA500',
    'CAUTION': '#FFD700',
    'CRITICAL': '#FF4C4C',
    'UNKNOWN': '#666666'
  };

  function loadChart(sensor) {
    const showUpper = document.getElementById('chkUpper')?.checked ?? true;
    const showLower = document.getElementById('chkLower')?.checked ?? true;
    const showCount = document.getElementById('chkCount')?.checked ?? true;
    const showRate = document.getElementById('chkRate')?.checked ?? true;
    const showLevel = document.getElementById('chkLevel')?.checked ?? true;

    fetch('/api/diagnosis-detail', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sensor })
    })
      .then(res => res.json())
      .then(data => {
        const datasets = [
          {
            label: 'Train',
            data: data.train.map((y, i) => ({ x: i, y })),
            borderColor: 'green',
            backgroundColor: 'green',
            showLine: false,
            pointRadius: 2
          },
          {
            label: 'Test',
            data: data.test.map((y, i) => ({ x: data.train.length + i, y })),
            borderColor: 'orange',
            backgroundColor: 'orange',
            showLine: false,
            pointRadius: 2
          }
        ];

        const totalLength = data.train.length + data.test.length;

        if (showUpper && data.upper !== null) {
          datasets.push({
            label: 'Upper Threshold',
            type: 'line',
            data: Array.from({ length: totalLength }, (_, i) => ({ x: i, y: data.upper })),
            borderColor: 'red',
            borderDash: [5, 5],
            fill: false,
            pointRadius: 0
          });
        }

        if (showLower && data.lower !== null) {
          datasets.push({
            label: 'Lower Threshold',
            type: 'line',
            data: Array.from({ length: totalLength }, (_, i) => ({ x: i, y: data.lower })),
            borderColor: 'blue',
            borderDash: [5, 5],
            fill: false,
            pointRadius: 0
          });
        }

        const titleParts = [data.name];
        if (showLevel) titleParts.push(`Level: ${data.error_level}`);
        if (showCount) titleParts.push(`Count: ${data.error_count}`);
        if (showRate) titleParts.push(`Std Rate: ${data.error_rate}`);
        const titleColor = levelColorMap[data.error_level] || '#333';

        if (chart) chart.destroy();
        chart = new Chart(chartCanvas, {
          type: 'scatter',
          data: { datasets },
          options: {
            responsive: true,
            maintainAspectRatio: false,  // 차트가 캔버스 사이즈에 맞춤
            plugins: {
              title: {
                display: true,
                text: titleParts.join(' | '),
                font: { size: 16, weight: '600' },  // 폰트 개선
                color: titleColor,
                padding: { top: 15, bottom: 10 }
              },
              legend: {
                display: true,
                position: 'bottom',
                align: 'center',
                labels: {
                  font: { size: 10 },
                  boxWidth: 12
                }
              }
            },
            scales: {
              x: { type: 'linear', title: { display: true, text: 'Index' } },
              y: { title: { display: true, text: data.name } }
            }
          }
        });
      });
  }

  const sensorType = 'maxTorque';
  const sensorAxis = '1';
  const initialSensor = `${sensorType}${sensorAxis}`;
  document.getElementById('sensorType').value = 'maxTorque';
  document.getElementById('sensorAxis').value = '1';
  document.getElementById('chkUpper').checked = true;
  document.getElementById('chkLower').checked = true;
  document.getElementById('chkCount').checked = true;
  document.getElementById('chkRate').checked = true;
  document.getElementById('chkLevel').checked = true;
  loadChart(initialSensor);

  const filterElements = [
    '#sensorType', '#sensorAxis',
    '#chkUpper', '#chkLower', '#chkCount', '#chkRate', '#chkLevel'
  ];
  filterElements.forEach(selector => {
    const el = document.querySelector(selector);
    if (el) {
      el.addEventListener('change', () => {
        const selectedSensorType = document.getElementById('sensorType')?.value || 'maxTorque';
        const selectedSensorAxis = document.getElementById('sensorAxis')?.value || '1';
        const sensor = `${selectedSensorType}${selectedSensorAxis}`;
        loadChart(sensor);
      });
    }
  });
});
