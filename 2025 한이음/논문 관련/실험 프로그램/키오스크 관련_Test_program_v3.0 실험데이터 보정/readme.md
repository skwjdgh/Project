음성 인식 정확도 비교 실험 프로그램 (v2.1)
1. 프로젝트 개요
이 프로젝트는 무인 민원 키오스크 환경을 가정하여, 다양한 전처리 기법이 Whisper STT 모델의 키워드 인식 정확도에 미치는 영향을 정량적으로 분석하기 위해 설계되었습니다. 효율성, 신뢰성, 안정성을 중심으로 개선되었습니다.

주요 기능 및 개선 사항
신뢰성 높은 Ground Truth: Input_data/text/united.csv 파일과 대조하여 유효한 키워드를 가진 파일만 실험에 포함시켜 결과의 신뢰도를 높였습니다.

고속 처리: 노이즈 제거 시 임시 파일을 생성하지 않고 메모리에서 직접 오디오 데이터를 처리하여 디스크 I/O 병목을 제거하고 실험 시간을 단축했습니다.

실험 재개 기능: 대규모 실험이 중단되어도 이전에 처리한 파일은 건너뛰고 중단된 지점부터 자동으로 실험을 재개합니다.

상세 로그: Results/experiment_log.txt에 실험 과정, 오류, 경고를 상세히 기록하여 추적 및 디버깅이 용이합니다.

2. 프로젝트 구조
.
├── Imp_Experiment.py         # 메인 실험 실행 스크립트
├── def_config.py             # 실험 환경 설정 파일
├── README.md                 # 프로젝트 설명서 (현재 파일)
├── requirements.txt          # 필요 라이브러리 목록
│
├── Input_data/
│   ├── text/
│   │   └── united.csv        # (필수) 문장/키워드 데이터 위치
│   ├── voice/                # (사용자 제공) 음성 파일 위치 1
│   └── test/                 # (사용자 제공) 음성 파일 위치 2
│
├── Results/
│   ├── experiment_log.txt    # 모든 과정과 오류를 기록하는 로그 파일
│   ├── detailed_results.csv  # 개별 실험 결과 (실험 재개 시 사용됨)
│   └── ...                   # (자동 생성) 분석 차트 및 요약 CSV
│
└── Utility/
    ├── func_tokenizer.py
    ├── func_noisecanceller.py
    ├── func_sorter.py
    └── func_visualization.py

3. 사용 방법
3.1. 환경 설정 및 데이터 준비
Python 3.8+ 환경에서 pip install -r requirements.txt 명령어로 필요 라이브러리를 설치합니다.

def_config.py 파일을 열어 모델 크기(WHISPER_MODEL) 등 실험 환경을 필요에 따라 수정합니다.

데이터 파일을 배치합니다.

united.csv 파일은 Input_data/text/ 폴더 안에 위치시켜야 합니다.

분석할 음성 파일들(.mp3, .wav)은 Input_data/voice/ 또는 Input_data/test/ 폴더에 넣습니다.

음성 파일명 규칙: 지역_키워드_연령_성별_목소리_인덱스.확장자 형식을 따라야 하며, 키워드는 united.csv의 종류 컬럼에 반드시 존재해야 합니다.

3.2. 실험 실행
터미널에서 다음 명령어를 실행합니다.

python Imp_Experiment.py

스크립트는 Results/detailed_results.csv 파일을 확인하여 이전에 처리된 파일은 건너뛰고 자동으로 이어서 진행합니다.

3.3. 결과 확인
실행이 완료되면 Results/ 폴더에서 생성된 결과물들을 확인합니다.

experiment_log.txt: 실험의 전 과정을 시간 순으로 확인할 수 있는 가장 중요한 로그 파일입니다.

accuracy_comparison.png: 조건별 최종 정확도를 시각적으로 비교할 수 있는 막대그래프입니다.

.csv 파일들: 상세 결과 및 요약 데이터를 담고 있습니다.