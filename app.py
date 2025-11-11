from flask import Flask, render_template, jsonify, request, send_from_directory 
import pymysql
import pandas as pd
from datetime import datetime,timedelta
from db_config import mysql  # DB 설정 분리되어 있다면 사용
from datetime import datetime, timedelta
import os
import re


# === Modification Info ===
# Date: 2025-09-01
# id: badalim
# Description: 유지보수 및 코드 정리 


# http://199.34.57.94:5000
app = Flask(__name__)
MYSQL_CONFIG = pymysql.connect(
        host='localhost',
        user='PRM01_HAIC',
        password='hanyangai@',
        db='gwai_cymechs',
        charset='utf8',
        cursorclass=pymysql.cursors.DictCursor
    )

sdCommand = "PICK"
sdStage = 3
sdArm = 2
axis_map = {'1': 'T1', '2': 'Z', '3': 'T2', '4': 'A', '5' : 'B'} # 숫자 → 축 이름으로 변환하는 매핑 함수 


# ============================================================
# 🧩 함수 정의 구간 (유틸, 데이터 처리 등)
# ============================================================

def summarize_last_month_data(): # Long-Term Trend를 확인하기 위한 함수. 2주 간격으로 min, max,std, mean 계산 후 'long_term_Trend'에 저장 
    # 1. DB 연결하여 가장 최신 날짜 조회
    conn = pymysql.connect(**mysql)
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT MAX(DATE(loggingDateTime)) AS latest_date FROM simple_sd_data")
            result = cursor.fetchone()
            if not result or not result['latest_date']:
                print("❗ loggingDateTime 기준 최신 날짜를 찾을 수 없습니다.")
                return
            today = result['latest_date']
    finally:
        conn.close()

    # 2. 날짜 계산 (최신일 기준 14일 전 ~ 하루 전)
    start_date = today - timedelta(days=14)
    end_date = today - timedelta(days=1)
    logging_group_date = end_date.strftime('%Y-%m-%d')

    # 3. 설정 값
    columns = ['maxTorque1', 'maxTorque2', 'maxTorque3','maxTorque4','maxTorque5',
               'minTorque1', 'minTorque2', 'minTorque3', 'minTorque4','minTorque5',
               'maxDuty1', 'maxDuty2', 'maxDuty3', 'maxDuty4', 'maxDuty5',
               'maxPosErr1', 'maxPosErr2','maxPosErr3', 'maxPosErr4', 'maxPosErr5',
               'gripOnTime', 'gripOffTime', 'inrangeTime', 'movingTime']

    # 4. 데이터 조회 및 집계
    conn = pymysql.connect(**mysql)
    try:
        with conn.cursor() as cursor:
            col_str = ', '.join(columns)
            sql = f"""
                SELECT {col_str}
                FROM simple_sd_data
                WHERE DATE(loggingDateTime) BETWEEN %s AND %s
                AND command = %s AND stage = %s AND arm = %s
            """
            cursor.execute(sql, (start_date, end_date, sdCommand, sdStage, sdArm))
            rows = cursor.fetchall()

            if not rows:
                print("❗ 조건에 맞는 데이터가 없습니다.")
                return

            df = pd.DataFrame(rows, columns=columns)

            # 5. INSERT 수행
            for col in columns:
                avg = round(df[col].mean(), 3)
                max_val = round(df[col].max(), 3)
                min_val = round(df[col].min(), 3)
                std = round(df[col].std(ddof=0), 3)

                insert_sql = """
                    INSERT INTO long_term_trend (
                        loggingDateTime_group, dataName, command, stage, arm, avg, min, max, std
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        avg = VALUES(avg),
                        min = VALUES(min),
                        max = VALUES(max),
                        std = VALUES(std)
                """
                cursor.execute(insert_sql, (
                    logging_group_date, col, sdCommand, sdStage, sdArm,
                    avg, min_val, max_val, std
                ))

        conn.commit()
        print(f"✅ long_term_trend 저장 완료: {logging_group_date}")
    except Exception as e:
        print("❌ 저장 중 오류:", e)
    finally:
        conn.close()

def log_start(file_path, message):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(file_path, "a") as f:
        f.write(f"[{now}] {message}\n")
        
# DB에서 가장 최근 저장일자를 기준으로 1년 이전 데이터를 삭제하여 데이터베이스 용량을 관리하는 함수 
def delete_old_data():
    conn = pymysql.connect(**mysql)
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # 최신 날짜 가져오기
            cursor.execute("SELECT MAX(DATE(loggingDateTime)) AS latest_date FROM simple_sd_data")
            result = cursor.fetchone()

            if not result or not result['latest_date']:
                print("❗ loggingDateTime 기준 최신 날짜를 찾을 수 없습니다.")
                return

            latest_date = result['latest_date']
            cutoff_date = latest_date - timedelta(days=365)

            # 오래된 데이터 삭제
            delete_query = "DELETE FROM simple_sd_data WHERE loggingDateTime < %s"
            cursor.execute(delete_query, (cutoff_date,))
            conn.commit()

            print(f"✅ Deleted records older than {cutoff_date}.")
            return "delete_old"

    except pymysql.MySQLError as err:
        print(f"❌ MySQL error: {err}")
        return "error"

    finally:
        conn.close()

# 서버 시작 시 1회만 수행
def get_oldest_date():
    conn = pymysql.connect(
        host='127.0.0.1',
        user='PRM01_HAIC',
        password='hanyangai@',
        db='gwai_cymechs',
        charset='utf8',
        cursorclass=pymysql.cursors.DictCursor
    )
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT MIN(loggingDateTime) AS min_date FROM simple_sd_data")
    result = cursor.fetchone()
    conn.close()
    return result['min_date'].strftime('%Y-%m-%d') if result['min_date'] else datetime.today().strftime('%Y-%m-%d')

def convert(sensor):
    # sensor 문자열 안에서 숫자 1자리(0~9)를 찾음
    match = re.search(r'(\d)', sensor)
    if match:
        axis = match.group(1)  # 예: '1', '2', '3'
        if axis in axis_map:
            # 첫 번째 숫자를 해당 축 이름으로 치환
            return axis_map[axis]
    return sensor

# 전역 변수로 저장
GLOBAL_START_DATE = get_oldest_date() # DB에서 가장 오래된 데이터의 날짜 
GLOBAL_END_DATE = datetime.today().strftime('%Y-%m-%d') # 현재 일자 반환

# 문자열을 datetime 객체로 변환 후 차이 계산
start_dt = datetime.strptime(GLOBAL_START_DATE, '%Y-%m-%d')
end_dt = datetime.strptime(GLOBAL_END_DATE, '%Y-%m-%d')
GLOBAL_DIFF = (end_dt - start_dt).days

# simple_sd_data에서 데이터를 불러와서 long_term_trend 디비에 저장하는 함수
# 6개월 주기로 디비 삭제, 1개월 주기로 계산 및 저장, 최대/최소/평균값 저장  
def aggregate_weekly_and_insert(sdCommand, sdStage, sdArm):
    print("aggregate_weekly_and_insert 수행 시작")

    # DB 연결
    conn = pymysql.connect(
        host='127.0.0.1',
        user='PRM01_HAIC',
        password='hanyangai@',
        db='gwai_cymechs',
        charset='utf8',
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        with conn.cursor() as cursor:
            # 원본 데이터 불러오기
            cursor.execute("""
                SELECT * FROM simple_sd_data
                WHERE maxTorque1 IS NOT NULL
                  AND minTorque2 != 999999
                  AND command = %s
                  AND stage = %s
                  AND arm = %s
                ORDER BY loggingDateTime ASC
            """, (sdCommand, sdStage, sdArm))
            rows = cursor.fetchall()

        df = pd.DataFrame(rows)
        if df.empty:
            print("No data found in simple_sd_data.")
            return

        # 날짜 → 주 단위 그룹핑
        df['loggingDateTime'] = pd.to_datetime(df['loggingDateTime'])
        df['loggingDateTime_group'] = df['loggingDateTime'].dt.to_period('W').apply(lambda r: r.start_time)

        # 집계 제외 컬럼
        exclude_cols = ['id', 'loggingDateTime', 'dateIndex', 'timeIndex']
        group_keys = ['loggingDateTime_group', 'command', 'stage', 'arm']
        value_cols = [col for col in df.columns if col not in exclude_cols + group_keys]

        # 평균 집계
        grouped = df.groupby(group_keys)[value_cols].mean().reset_index()

        # 삽입
        with conn.cursor() as cursor:
            for _, row in grouped.iterrows():
                insert_columns = group_keys + value_cols
                placeholders = ', '.join(['%s'] * len(insert_columns))
                update_clause = ', '.join([f"{col} = VALUES({col})" for col in value_cols])

                insert_sql = f"""
                    INSERT INTO long_term ({', '.join(insert_columns)})
                    VALUES ({placeholders})
                    ON DUPLICATE KEY UPDATE {update_clause}
                """

                insert_values = [row[col] if not pd.isna(row[col]) else None for col in insert_columns]
                cursor.execute(insert_sql, tuple(insert_values))

            conn.commit()
            print("✅ long_term 저장 완료.")

    except Exception as e:
        print("❌ Error:", e)

    finally:
        conn.close()
        
# ✅ 센서 이름별 색상 지정 함수 (간단히 고정 팔레트 사용)
def get_color_for_sensor(sensor):
    color_palette = {
        'gripOnTime': '#4CAF50',
        'gripOffTime': '#2196F3',
        'movingTime': '#FF9800',
        'inrangeTime': '#9C27B0',
        'maxTorque1': '#F44336',
        'maxTorque2': '#03A9F4',
        'minTorque1': '#795548'
        # 필요 시 추가 정의
    }
    return color_palette.get(sensor, '#666')


# ============================================================
# 🌐 라우터 정의 (화면 라우트)
# ============================================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('elements/Monitoring.html')

@app.route('/monitoring')
def monitoring():
    return render_template('elements/Monitoring.html')

@app.route('/maintenance')
def maintenance():
    return render_template('elements/Maintenance.html')

@app.route('/authentication/login')
def login():
    return render_template('pages/login-v1.html')

@app.route('/authentication/register')
def register():
    return render_template('pages/register-v1.html')

@app.route('/healthmonitoring/maxtorque')
def maxTorque():
    return render_template('elements/MaxTorque.html',start_date=GLOBAL_START_DATE, end_date=GLOBAL_END_DATE, date_diff= GLOBAL_DIFF)

@app.route('/healthmonitoring/mintorque')
def minTorque():
    return render_template('elements/MinTorque.html',start_date=GLOBAL_START_DATE, end_date=GLOBAL_END_DATE, date_diff= GLOBAL_DIFF)

@app.route('/healthmonitoring/maxduty')
def maxDuty():
    return render_template('elements/MaxDuty.html',start_date=GLOBAL_START_DATE, end_date=GLOBAL_END_DATE, date_diff= GLOBAL_DIFF)

@app.route('/healthmonitoring/maxposerr')
def maxPoserr():
    return render_template('elements/MaxPosErr.html',start_date=GLOBAL_START_DATE, end_date=GLOBAL_END_DATE, date_diff= GLOBAL_DIFF)

@app.route('/healthmonitoring/gripontime')
def gripOntime():
    return render_template('elements/GripTime.html',start_date=GLOBAL_START_DATE, end_date=GLOBAL_END_DATE, date_diff= GLOBAL_DIFF)

@app.route('/healthmonitoring/inrangetime')
def inrangeTime():
    return render_template('elements/InrangeTime.html',start_date=GLOBAL_START_DATE, end_date=GLOBAL_END_DATE, date_diff= GLOBAL_DIFF)

@app.route('/healthmonitoring/runtime')
def movingTime():
    return render_template('elements/movingTime.html',start_date=GLOBAL_START_DATE, end_date=GLOBAL_END_DATE, date_diff= GLOBAL_DIFF)

@app.route('/healthmonitoring/pdm')
def Pdm():
    return render_template('elements/Pdm.html')

@app.route('/healthmonitoring/mastercode')
def masterCode():
    return render_template('elements/masterCode.html')

@app.route('/test')
def test():
    return render_template('index_temp.html')

@app.route('/longTerm_maxTorque')
def long_term_max_torque():
    return render_template('elements/LMaxTorque.html',start_date=GLOBAL_START_DATE, end_date=GLOBAL_END_DATE, date_diff= GLOBAL_DIFF)

@app.route('/longTerm_minTorque')
def long_term_min_torque():
    return render_template('elements/LMinTorque.html',start_date=GLOBAL_START_DATE, end_date=GLOBAL_END_DATE, date_diff= GLOBAL_DIFF)

@app.route('/longTerm_maxduty')
def long_term_max_duty():
    return render_template('elements/LMaxDuty.html',start_date=GLOBAL_START_DATE, end_date=GLOBAL_END_DATE, date_diff= GLOBAL_DIFF)

@app.route('/longTerm_maxPoserr')
def long_term_max_Poserr():
    return render_template('elements/LMaxPosErr.html',start_date=GLOBAL_START_DATE, end_date=GLOBAL_END_DATE, date_diff= GLOBAL_DIFF)

@app.route('/longTerm_gripOntime')
def long_term_gripOntime():
    return render_template('elements/LGriptime.html',start_date=GLOBAL_START_DATE, end_date=GLOBAL_END_DATE, date_diff= GLOBAL_DIFF)

@app.route('/longTerm_inrangetime')
def long_term_inrangetime():
    return render_template('elements/LInrangeTime .html',start_date=GLOBAL_START_DATE, end_date=GLOBAL_END_DATE, date_diff= GLOBAL_DIFF)

@app.route('/longTerm_movingtime')
def long_term_movingtime():
    return render_template('elements/LmovingTime.html',start_date=GLOBAL_START_DATE, end_date=GLOBAL_END_DATE, date_diff= GLOBAL_DIFF)


# ============================================================
# 🌐 라우터 정의 (API)
# ============================================================

@app.route('/manuals/<path:filename>') 
def download_manual(filename):
    manuals_dir = os.path.join(app.root_path, 'static','manuals')
    return send_from_directory(manuals_dir,filename, as_attachment = True)

# [1] : chart.js 사용 API, 실시간 경향성 시각화     
@app.route('/api/sensor-data', methods=['POST'])
def filter_sensor_data():
    params = request.get_json() 

    start_date = params.get('startDate')
    end_date = params.get('endDate')
    command = params.get('command')
    stage = params.get('stage')
    arm = params.get('arm')
    sensors = params.get('sensors', [])
    sensor_colors = {'T1': '#FF6B6B' , 'Z' : 'orange', 'T2': '#FFD700', 'A': '#4CD964' , 'B': '#4A90E2', 'gripOnTime' : '#FFD700', 'gripOffTime' : '#4A90E2', 'movingTime' : '#FF6B6B', 'inrangeTime' : '#4CD964'}
    sensor_units = {
    'gripOnTime': 'sec', 'gripOffTime': 'sec', 'movingTime': 'sec', 'inrangeTime': 'sec', 'maxPosErr1': 'ecnt','maxPosErr2': 'ecnt','maxPosErr3': 'ecnt','maxPosErr4': 'ecnt','maxPosErr5': 'ecnt'
    }
    
    # end_date 처리: 하루 더해 다음날로 만들어 포함시키기
    end_date_str = None
    if end_date:
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        end_date_str = end_date_obj.strftime('%Y-%m-%d')

    conn = pymysql.connect(**mysql)
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    conditions = ["minTorque2 != 999999"]
    if start_date:
        conditions.append(f"loggingDateTime >= '{start_date}'")
    if end_date_str:
        conditions.append(f"loggingDateTime < '{end_date_str}'")  # end_date 포함 처리
    if command:
        conditions.append(f"command = '{command}'")
    if stage:
        conditions.append(f"stage = {stage}")
    if arm:
        conditions.append(f"arm = {arm}")

    where_clause = " AND ".join(conditions)
    columns = ", ".join(["loggingDateTime"] + sensors)

    # 최신순으로 70,000개를 가져옴
    query = f"SELECT {columns} FROM simple_sd_data WHERE {where_clause} ORDER BY loggingDateTime DESC LIMIT 70000"
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    # 시간 오름차순으로 재정렬
    rows.sort(key=lambda x: x['loggingDateTime'])

    labels = [row['loggingDateTime'].strftime('%Y-%m-%d') for row in rows]
    datasets = []

    for sensor in sensors:
        temp_sensor = convert(sensor)
        datasets.append({
            "name": re.sub(r'\d+', '', sensor),
            "axis_name": temp_sensor,
            "values": [row[sensor] for row in rows],
            "color": sensor_colors[temp_sensor],
            "unit": sensor_units.get(sensor, '%')
        })

    return jsonify({"labels": labels, "datasets": datasets})

# 장기 경향성 시각화 
@app.route('/api/trend-data', methods=['POST'])
def get_trend_data():
    try:
        # 1. 요청 파라미터 추출
        params = request.get_json()
        command = params.get('command')
        stage = params.get('stage')
        arm = params.get('arm')
        sensors = params.get('sensors', [])
        stat = params.get('stat', 'avg')  # 기본은 평균

        if not sensors or stat not in ['avg', 'min', 'max', 'std']:
            return jsonify({'labels': [], 'datasets': []})

        # 2. 색상 및 단위 정의
        sensor_colors = {
            'T1': '#FF6B6B', 'Z': 'orange', 'T2': '#FFD700',
            'A': '#4CD964', 'B': '#4A90E2',
            'gripOnTime': '#FFD700', 'gripOffTime': '#4A90E2',
            'movingTime': '#FF6B6B', 'inrangeTime': '#4CD964'
        }

        sensor_units = {
            'gripOnTime': 'sec', 'gripOffTime': 'sec',
            'movingTime': 'sec', 'inrangeTime': 'sec',
            'maxPosErr1': 'ecnt', 'maxPosErr2': 'ecnt',
            'maxPosErr3': 'ecnt', 'maxPosErr4': 'ecnt',
            'maxPosErr5': 'ecnt'
        }

        # 3. DB 연결
        conn = pymysql.connect(
            host='127.0.0.1',
            user='PRM01_HAIC',
            password='hanyangai@',
            db='gwai_cymechs',
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor
        )
        cursor = conn.cursor()

        datasets = []
        labels = []

        # 4. 센서별 반복 쿼리
        for sensor in sensors:
            query = f"""
                SELECT loggingDateTime_group, {stat} AS `{sensor}`
                FROM long_term_trend
                WHERE dataName = %s AND command = %s AND stage = %s AND arm = %s
                ORDER BY loggingDateTime_group ASC
            """
            cursor.execute(query, (sensor, sdCommand, sdStage, sdArm))
            rows = cursor.fetchall()
            if not rows:
                print(f"❗ 데이터 없음: ({(sensor, sdCommand, sdStage, sdArm)})")
                continue

            df = pd.DataFrame(rows)
            df['loggingDateTime_group'] = pd.to_datetime(df['loggingDateTime_group'])

            if not labels:
                labels = df['loggingDateTime_group'].dt.strftime('%Y-%m-%d').tolist()

            values = df[sensor].fillna(0).tolist()
            base_sensor = re.sub(r'\d+', '', sensor)
            temp_sensor = convert(sensor) if 'convert' in globals() else base_sensor

            datasets.append({
                'name': base_sensor,
                'axis_name': temp_sensor,
                'values': values,
                'color': sensor_colors.get(temp_sensor, '#888'),
                'unit': sensor_units.get(sensor, '%')
            })

        conn.close()
        return jsonify({'labels': labels, 'datasets': datasets})

    except Exception as e:
        print(f"❌ /api/trend-data error: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500


# 날짜를 받아오는 API
@app.route('/api/diagnosis-min-date')
def get_min_logging_date():
    conn = pymysql.connect(**mysql)
    cursor = conn.cursor()
    cursor.execute("SELECT MIN(loggingDateTime) FROM simple_sd_data")
    min_date = cursor.fetchone()[0]
    conn.close()
    return jsonify({'min_date': min_date.strftime('%Y-%m-%d')})

# NOTE : PDM.html 페이지 
@app.route('/api/diagnosis-detail', methods=['POST'])
def diagnosis_detail():
    data = request.json
    sensor = data.get('sensor')

    conn = pymysql.connect(
        host='127.0.0.1',
        user='PRM01_HAIC',
        password='hanyangai@',
        db='gwai_cymechs',
        charset='utf8',
        cursorclass=pymysql.cursors.DictCursor
    )
    cursor = conn.cursor()

    # 최근 데이터 6000개 기준
    SD_TRAIN_COUNT = 3000

    # 데이터 조회
    query = f"""
        SELECT loggingDateTime, {sensor}
        FROM simple_sd_data
        WHERE {sensor} IS NOT NULL
        AND minTorque2 != 999999
        AND Command = %s
        AND stage = %s
        AND arm = %s
        ORDER BY loggingDateTime ASC
    """
    cursor.execute(query, (sdCommand, sdStage, sdArm))
    rows = cursor.fetchall()
    df = pd.DataFrame(rows)

    if df.empty:
        return jsonify({'error': 'No data found'}), 404

    train_data = df[sensor][:SD_TRAIN_COUNT].tolist()
    test_data = df[sensor][SD_TRAIN_COUNT:].tolist()

    # threshold
    cursor.execute("""
        SELECT 
            (SELECT value FROM simple_thresholds WHERE sd_name = %s AND metric_type = 'upper' ORDER BY logging_datetime DESC LIMIT 1) AS upper,
            (SELECT value FROM simple_thresholds WHERE sd_name = %s AND metric_type = 'lower' ORDER BY logging_datetime DESC LIMIT 1) AS lower
    """, (sensor, sensor))
    th = cursor.fetchone()
    upper = th['upper']
    lower = th['lower']

    # 진단 결과
    cursor.execute("""
        SELECT error_count, error_rate, error_level
        FROM simple_diagnosis_result
        WHERE sensor_name = %s
        ORDER BY diagnosis_time DESC
        LIMIT 1
    """, (sensor,))
    diag = cursor.fetchone() or {}

    cursor.close()
    conn.close()

    return jsonify({
        'name': sensor,
        'train': train_data,
        'test': test_data,
        'upper': upper,
        'lower': lower,
        'error_level': diag.get('error_level', 'UNKNOWN'),
        'error_count': diag.get('error_count', -1),
        'error_rate': diag.get('error_rate', -1.0)
    })
    
# [2] : monitoring.js 
@app.route('/api/latest-data', methods=['POST'])
def latest_data():
    data = request.json
    data_type = data.get('data_type')  # 예: "max_position" 또는 "inrange_time"

    conn = pymysql.connect(
        host='127.0.0.1',
        user='PRM01_HAIC',
        port=3306,
        password='hanyangai@',
        db='gwai_cymechs',
        charset='utf8',
        cursorclass=pymysql.cursors.DictCursor
    )
    cursor = conn.cursor()

    # 데이터별 쿼리 구분
    if data_type == 'gripOnTime':
        query = """
            SELECT loggingDateTime, gripOnTime, gripOffTime
            FROM simple_sd_data where Command = %s And stage = %s and arm = %s
            ORDER BY loggingDateTime DESC LIMIT 1
        """
    elif data_type == 'movingTime':
        query = """
            SELECT loggingDateTime, movingTime
            FROM simple_sd_data where Command = %s And stage = %s and arm = %s
            ORDER BY loggingDateTime DESC LIMIT 1
        """
    elif data_type == 'maxTorque':
        query = """
            SELECT loggingDateTime, maxTorque1,maxTorque2,maxTorque3,maxTorque4,maxTorque5
            FROM simple_sd_data where Command = %s And stage = %s and arm = %s
            ORDER BY loggingDateTime DESC LIMIT 1
        """
    elif data_type == 'maxDuty':
        query = """
            SELECT loggingDateTime, maxDuty1,maxDuty2,maxDuty3,maxDuty4,maxDuty5
            FROM simple_sd_data where Command = %s And stage = %s and arm = %s
            ORDER BY loggingDateTime DESC LIMIT 1
        """
    elif data_type == 'maxPosErr':
        query = """
            SELECT loggingDateTime,maxPosErr1,maxPosErr2,maxPosErr3,maxPosErr4,maxPosErr5
            FROM simple_sd_data where Command = %s And stage = %s and arm = %s
            ORDER BY loggingDateTime DESC LIMIT 1
        """
    elif data_type == 'inrangeTime':
        query = """
            SELECT loggingDateTime,inrangeTime
            FROM simple_sd_data where Command = %s And stage = %s and arm = %s
            ORDER BY loggingDateTime DESC LIMIT 1
        """
    elif data_type == 'cpuTemp':
        query = """
            SELECT cpuTemp
            FROM simple_sd_data where Command = %s And stage = %s and arm = %s
            ORDER BY loggingDateTime DESC LIMIT 1
        """
    elif data_type == 'humidity':
        query = """
            SELECT humidity
            FROM simple_sd_data where Command = %s And stage = %s and arm = %s
            ORDER BY loggingDateTime DESC LIMIT 1
        """
    else:
        return jsonify({"error": "Invalid data type"})

    cursor.execute(query, (sdCommand, sdStage, sdArm))
    row = cursor.fetchone() or {}
    # print(f"📌 {data_type} 결과:", row)
    cursor.close()
    conn.close()
    return jsonify(row)

# PDM
# [1] : chart.js 사용 API   
@app.route('/api/error-level-data')
def error_level_data():
    conn = pymysql.connect(
        host='127.0.0.1',
        user='PRM01_HAIC',
        port=3306,
        password='hanyangai@',
        db='gwai_cymechs',
        charset='utf8',
        cursorclass=pymysql.cursors.DictCursor
    )
    cursor = conn.cursor()

    # 에러 레벨별 개수 가져오기
    query = """
        SELECT error_level, COUNT(*) as count
        FROM simple_diagnosis_result
        GROUP BY error_level
    """
    cursor.execute(query)
    results = cursor.fetchall()

    # 전체 개수 계산
    total_count = sum(row['count'] for row in results) or 1  # total_count가 0인 경우 방지
    data = { 'OK': 0, 'CAUTION': 0, 'WARNING': 0, 'CRITICAL': 0 }

    for row in results:
        level = row['error_level'].upper() if row['error_level'] else 'UNKNOWN'
        count = row['count']
        if level in data:
            data[level] = round((count / total_count) * 100, 2)  # 퍼센트 계산

    cursor.close()
    conn.close()
    return jsonify(data)

@app.route('/api/diagnosis-filtered', methods=['POST'])
def diagnosis_filtered():
    data = request.json
    level = data.get('level', '').upper()  # 요청으로 error_level 받기

    conn = pymysql.connect(
        host='127.0.0.1',
        user='PRM01_HAIC',
        port=3306,
        password='hanyangai@',
        db='gwai_cymechs',
        charset='utf8',
        cursorclass=pymysql.cursors.DictCursor
    )
    cursor = conn.cursor()

    query = """
        SELECT diagnosis_time, robot_id, sensor_name, error_count, error_rate, error_level, remark
        FROM simple_diagnosis_result
        WHERE error_level = %s
        ORDER BY diagnosis_time DESC
    """
    cursor.execute(query, (level,))
    results = cursor.fetchall()

    cursor.close()
    conn.close()
    return jsonify(results)

    
    
if __name__ == '__main__':
    log_start("/home/pi/app_log.txt", "app.py auto-execution completed")
    # aggregate_weekly_and_insert(sdCommand=sdCommand, sdStage=sdStage, sdArm=sdArm)
    app.run(host = '0.0.0.0', port = 5000, debug=True) 
    
