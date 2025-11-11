// Last Updated: 2025-06-12 by lim bada

const updateInterval = 10000

const keyMap = {
  loggingDateTime: 'Logging Date',
  gripOnTime: 'gripOnTime',
  gripOffTime: 'gripOffTime',
  movingTime: 'MovingTime',
  command: 'Command',
  stage: 'Stage',
  maxTorque1 : 'T1',
  maxTorque2 : 'Z',
  maxTorque3 : 'T2',
  maxTorque4 : 'Lower (A Arm)',
  maxTorque5 : 'Upper(B Arm)',
  maxDuty1 : 'T1',
  maxDuty2 : 'Z',
  maxDuty3 : 'T2',
  maxDuty4 : 'Lower (A Arm)',
  maxDuty5 : 'Upper (B Arm)',
  maxPosErr1 : 'T1',
  maxPosErr2 : 'Z',
  maxPosErr3 : 'T2', 
  maxPosErr4 : 'Lower (A Arm)',
  maxPosErr5 : 'Upper (B Arm)',


};

function updateEnvData() {
  // CPU 온도 가져오기
  fetch('/api/latest-data', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ data_type: 'cpuTemp' })
  })
  .then(response => response.json())
  .then(tempData => {
    const cpuTemp = tempData.cpuTemp ?? '-';

    // 습도 가져오기
    fetch('/api/latest-data', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ data_type: 'humidity' })
    })
    .then(response => response.json())
    .then(humidityData => {
      const humidity = humidityData.humidity ?? '-';

      // 화면에 업데이트
      document.getElementById('envData').textContent = `온도: ${cpuTemp} ℃ | 습도: ${humidity} %`;
    });
  });
}


function loadData(dataType, elementId) {
  fetch('/api/latest-data', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ data_type: dataType })
  })
  .then(response => response.json())
  .then(data => {
    const tbody = document.getElementById(elementId);
    if (!tbody || !data) return;

    let html = '';

    // loggingDateTime을 먼저 출력하고 나머지 출력
    const keys = Object.keys(data);
    if (keys.includes('loggingDateTime')) {
      const date = new Date(data['loggingDateTime']);
      const options = { year: 'numeric', month: 'long', day: 'numeric', weekday: 'short' };
      const displayValue = date.toLocaleDateString('ko-KR', options);
      html += `<tr><th>${keyMap['loggingDateTime'] || 'loggingDateTime'}</th><td>${displayValue}</td></tr>`;
    }

    keys.filter(key => key !== 'loggingDateTime').forEach(key => {
      const displayKey = keyMap[key] || key;
      const value = data[key];
      html += `<tr><th>${displayKey}</th><td>${value}</td></tr>`;
    });

    tbody.innerHTML = html;
  });
}

function updateAllData() {
    // 갱신 시각 갱신
    const now = new Date().toLocaleString();
    document.getElementById('lastUpdated').textContent = `Last Updated: ${now}`;

    // 데이터 호출
    loadData('gripOnTime', 'latestGripOnTime');
    loadData('movingTime', 'latestMovingTime');

    loadData('maxTorque', 'latestMaxTorque');
    loadData('maxDuty', 'latestMaxDuty');

    loadData('maxPosErr', 'latestMaxPosition');
    loadData('inrangeTime', 'latestMaxInrangeTime');
}

// 페이지 로드 시 초기화
updateEnvData();
// 10초마다 자동 업데이트 (원하는 주기로 설정)
setInterval(updateEnvData, updateInterval)

// 최초 로드
updateAllData();
// 3초마다 자동 갱신
setInterval(updateAllData, updateInterval);

