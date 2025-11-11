function formatKoreanDate(utcString) {
  const date = new Date(utcString);
  const options = { year: 'numeric', month: 'long', day: 'numeric', weekday: 'short' };
  return date.toLocaleDateString('ko-KR', options);
}

document.addEventListener('DOMContentLoaded', () => {
  const levels = ['CRITICAL', 'WARNING', 'CAUTION'];

  function getColor(level) {
    switch (level) {
      case 'CRITICAL': return '#FF4C4C';   // 빨강
      case 'WARNING': return '#FFA500';    // 주황
      case 'CAUTION': return '#FFD700';    // 노랑
      case 'OK': return '#4CAF50';         // 초록
      default: return '#000';              // 기본 검정
    }
  }

  function loadDiagnosisData(level) {
    fetch('/api/diagnosis-filtered', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ level })
    })
    .then(response => response.json())
    .then(data => {
      const container = document.querySelector(`#analytics-tab-${levels.indexOf(level)+1}-pane ul`);
      container.innerHTML = '';

      // 최근 7개 데이터만 표시
      const latestData = data.slice(0, 7);

      latestData.forEach(item => {
        container.innerHTML += `
          <li class="list-group-item">
              <div><span class="label-key" style="color: ${getColor(item.error_level)};">진단 시각:</span> ${formatKoreanDate(item.diagnosis_time)}</div>
              <div><span class="label-key" style="color: ${getColor(item.error_level)};">로봇 & 센서:</span> ${item.robot_id || 'N/A'} | ${item.sensor_name}</div>
              <div><span class="label-key" style="color: ${getColor(item.error_level)};">결과:</span> Count: ${item.error_count}, Rate: ${item.error_rate}%</div>
          </li>`;
      });
    });
  }

  // 초기 로딩 시 CRITICAL 데이터 출력
  loadDiagnosisData('CRITICAL');

  levels.forEach(level => {
    document.getElementById(`analytics-tab-${levels.indexOf(level)+1}`).addEventListener('click', () => {
      loadDiagnosisData(level);
    });
  });
});
