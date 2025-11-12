#!/usr/bin/env bash
set -euo pipefail

### ==== 1. 설정 값 설정  ====
DB_NAME="gwai_cymechs"
DB_USER="PRM01_HAIC"
DB_PASS='hanyangai@'
DB_HOST="127.0.0.1"

### ==== 2. 파일명 설정  ====
# 시드(덤프) 파일: 파일명이 다르면 여기만 수정
SEED_FILE="./sample_data_2025.sql"
APPLY_SEED=${APPLY_SEED:-1}   # 1=시드 적용, 0=시드 적용 건너뛰기

### ==== 출력 유틸 ====
warn() { echo -e "\033[1;33m[!]\033[0m $*"; }
die()  { echo -e "\033[1;31m[✗]\033[0m $*"; exit 1; }

### ==== 0) MariaDB 설치 및 기동 ====
say "Install & start MariaDB (server/client)…"
sudo apt update -y
sudo apt install -y mariadb-server mariadb-client || die "apt install failed"
sudo systemctl enable --now mariadb

### ==== 1) DB/계정/권한 + 테이블 생성까지 한 번에 ====
say "Apply DB, user/grants, and tables…"
sudo mariadb <<'SQL'
SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;

-- 1) DB 생성
CREATE DATABASE IF NOT EXISTS gwai_cymechs DEFAULT CHARACTER SET utf8mb4;

-- 2) 계정 생성 (localhost + 127.0.0.1)
CREATE USER IF NOT EXISTS 'PRM01_HAIC'@'localhost'  IDENTIFIED BY 'hanyangai@';
CREATE USER IF NOT EXISTS 'PRM01_HAIC'@'127.0.0.1'  IDENTIFIED BY 'hanyangai@';

ALTER USER 'PRM01_HAIC'@'localhost'  IDENTIFIED BY 'hanyangai@';
ALTER USER 'PRM01_HAIC'@'127.0.0.1'  IDENTIFIED BY 'hanyangai@';

GRANT ALL PRIVILEGES ON gwai_cymechs.* TO 'PRM01_HAIC'@'localhost';
GRANT ALL PRIVILEGES ON gwai_cymechs.* TO 'PRM01_HAIC'@'127.0.0.1';
FLUSH PRIVILEGES;

USE gwai_cymechs;

-- ========== 1) long_term_trend ==========
CREATE TABLE IF NOT EXISTS `long_term_trend` (
  `loggingDateTime_group` date NOT NULL,
  `dataName` varchar(50) NOT NULL,
  `command` varchar(20) NOT NULL,
  `stage` int(11) NOT NULL,
  `arm` int(11) NOT NULL,
  `avg` float DEFAULT NULL,
  `min` float DEFAULT NULL,
  `max` float DEFAULT NULL,
  `std` float DEFAULT NULL,
  PRIMARY KEY (`loggingDateTime_group`,`dataName`,`command`,`stage`,`arm`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- ========== 2) simple_diagnosis_result ==========
CREATE TABLE IF NOT EXISTS `simple_diagnosis_result` (
  `robot_id` text DEFAULT NULL,
  `sensor_name` text DEFAULT NULL,
  `error_count` int(11) DEFAULT NULL,
  `error_rate` double DEFAULT NULL,
  `error_level` text DEFAULT NULL,
  `diagnosis_time` datetime DEFAULT NULL,
  `remark` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- ========== 3) simple_sd_data ==========
CREATE TABLE IF NOT EXISTS `simple_sd_data` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `loggingDateTime` datetime DEFAULT NULL,
  `dateIndex` int(11) DEFAULT NULL,
  `timeIndex` int(11) DEFAULT NULL,
  `command` text DEFAULT NULL,
  `stage` int(11) DEFAULT NULL,
  `arm` int(11) DEFAULT NULL,
  `slot` int(11) DEFAULT NULL,
  `cpuTemp` double DEFAULT NULL,
  `robotTemp` double DEFAULT NULL,
  `humidity` double DEFAULT NULL,
  `vibeX` double DEFAULT NULL,
  `vibeY` double DEFAULT NULL,
  `vibeZ` double DEFAULT NULL,
  `gripOnTime` double DEFAULT NULL,
  `gripOffTime` double DEFAULT NULL,
  `movingTime` double DEFAULT NULL,
  `inrangeTime` double DEFAULT NULL,
  `maxTorque1` double DEFAULT NULL,
  `maxTorque2` double DEFAULT NULL,
  `maxTorque3` double DEFAULT NULL,
  `maxTorque4` double DEFAULT NULL,
  `maxTorque5` double DEFAULT NULL,
  `maxTorque6` double DEFAULT NULL,
  `maxTorque7` double DEFAULT NULL,
  `maxTorque8` double DEFAULT NULL,
  `minTorque1` double DEFAULT NULL,
  `minTorque2` double DEFAULT NULL,
  `minTorque3` double DEFAULT NULL,
  `minTorque4` double DEFAULT NULL,
  `minTorque5` double DEFAULT NULL,
  `minTorque6` double DEFAULT NULL,
  `minTorque7` double DEFAULT NULL,
  `minTorque8` double DEFAULT NULL,
  `maxDuty1` double DEFAULT NULL,
  `maxDuty2` double DEFAULT NULL,
  `maxDuty3` double DEFAULT NULL,
  `maxDuty4` double DEFAULT NULL,
  `maxDuty5` double DEFAULT NULL,
  `maxDuty6` double DEFAULT NULL,
  `maxDuty7` double DEFAULT NULL,
  `maxDuty8` double DEFAULT NULL,
  `maxPosErr1` double DEFAULT NULL,
  `maxPosErr2` double DEFAULT NULL,
  `maxPosErr3` double DEFAULT NULL,
  `maxPosErr4` double DEFAULT NULL,
  `maxPosErr5` double DEFAULT NULL,
  `maxPosErr6` double DEFAULT NULL,
  `maxPosErr7` double DEFAULT NULL,
  `maxPosErr8` double DEFAULT NULL,
  `encCommError1` double DEFAULT NULL,
  `encCommError2` double DEFAULT NULL,
  `encCommError3` double DEFAULT NULL,
  `encCommError4` double DEFAULT NULL,
  `encCommError5` double DEFAULT NULL,
  `encCommError6` double DEFAULT NULL,
  `encCommError7` double DEFAULT NULL,
  `encCommError8` double DEFAULT NULL,
  `retention` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

-- ========== 4) simple_thresholds ==========
CREATE TABLE IF NOT EXISTS `simple_thresholds` (
  `sd_name` text DEFAULT NULL,
  `metric_type` text DEFAULT NULL,
  `value` double DEFAULT NULL,
  `logging_datetime` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

-- ========== 5) simple_ui_data ==========
CREATE TABLE IF NOT EXISTS `simple_ui_data` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `loggingDateTime` datetime DEFAULT NULL,
  `dateIndex` int(11) DEFAULT NULL,
  `timeIndex` int(11) DEFAULT NULL,
  `command` text DEFAULT NULL,
  `stage` int(11) DEFAULT NULL,
  `arm` int(11) DEFAULT NULL,
  `slot` int(11) DEFAULT NULL,
  `cpuTemp` double DEFAULT NULL,
  `robotTemp` double DEFAULT NULL,
  `humidity` double DEFAULT NULL,
  `vibeX` double DEFAULT NULL,
  `vibeY` double DEFAULT NULL,
  `vibeZ` double DEFAULT NULL,
  `gripOnTime` double DEFAULT NULL,
  `gripOffTime` double DEFAULT NULL,
  `movingTime` double DEFAULT NULL,
  `inrangeTime` double DEFAULT NULL,
  `maxTorque1` double DEFAULT NULL,
  `maxTorque2` double DEFAULT NULL,
  `maxTorque3` double DEFAULT NULL,
  `maxTorque4` double DEFAULT NULL,
  `maxTorque5` double DEFAULT NULL,
  `maxTorque6` double DEFAULT NULL,
  `maxTorque7` double DEFAULT NULL,
  `maxTorque8` double DEFAULT NULL,
  `minTorque1` double DEFAULT NULL,
  `minTorque2` double DEFAULT NULL,
  `minTorque3` double DEFAULT NULL,
  `minTorque4` double DEFAULT NULL,
  `minTorque5` double DEFAULT NULL,
  `minTorque6` double DEFAULT NULL,
  `minTorque7` double DEFAULT NULL,
  `minTorque8` double DEFAULT NULL,
  `maxDuty1` double DEFAULT NULL,
  `maxDuty2` double DEFAULT NULL,
  `maxDuty3` double DEFAULT NULL,
  `maxDuty4` double DEFAULT NULL,
  `maxDuty5` double DEFAULT NULL,
  `maxDuty6` double DEFAULT NULL,
  `maxDuty7` double DEFAULT NULL,
  `maxDuty8` double DEFAULT NULL,
  `maxPosErr1` double DEFAULT NULL,
  `maxPosErr2` double DEFAULT NULL,
  `maxPosErr3` double DEFAULT NULL,
  `maxPosErr4` double DEFAULT NULL,
  `maxPosErr5` double DEFAULT NULL,
  `maxPosErr6` double DEFAULT NULL,
  `maxPosErr7` double DEFAULT NULL,
  `maxPosErr8` double DEFAULT NULL,
  `encCommError1` double DEFAULT NULL,
  `encCommError2` double DEFAULT NULL,
  `encCommError3` double DEFAULT NULL,
  `encCommError4` double DEFAULT NULL,
  `encCommError5` double DEFAULT NULL,
  `encCommError6` double DEFAULT NULL,
  `encCommError7` double DEFAULT NULL,
  `encCommError8` double DEFAULT NULL,
  `retention` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

COMMIT;
SQL

### ==== 2) (옵션) 시드 파일 적용 ====
if [[ "$APPLY_SEED" = "1" && -f "$SEED_FILE" ]]; then
  say "Apply seed file: $SEED_FILE"
  MYSQL_PWD="$DB_PASS" mysql --no-defaults --protocol=TCP \
    -h "$DB_HOST" -u "$DB_USER" "$DB_NAME" < "$SEED_FILE" || die "seed apply failed"
else
  warn "Seed file not applied (APPLY_SEED=$APPLY_SEED, file=$SEED_FILE)"
fi

### ==== 3) 검증 ====
say "Verify: list tables & long_term_trend count"
MYSQL_PWD="$DB_PASS" mysql --no-defaults --protocol=TCP \
  -h "$DB_HOST" -u "$DB_USER" "$DB_NAME" -e "SHOW TABLES; SELECT COUNT(*) AS cnt_ltt FROM long_term_trend;"

say "All done ✅  DB=$DB_NAME  USER=$DB_USER"
