# Menu OCR Report Toolkit

Bo cong cu nay bo sung cac phan con thieu theo brief PDF ma khong sua bat ky dong code nao trong source hien co.

## Bao gom

- Tao `manifest` dataset va chia `dev/test`
- Validate JSON theo `schema_v1`
- Chay benchmark tren prediction da co
- Tinh metric:
  - `field_accuracy_name`
  - `field_accuracy_price`
  - `field_accuracy_category`
  - `item_recall`
  - `item_precision`
  - `hallucination_rate`
  - `structure_correctness`
  - `latency_ms`
  - `auto_publish_acceptance`
- Hieu chinh `guardrail` va tao bang `coverage vs accuracy`
- Tao `weekly report` va `final report` markdown
- Gom nhieu run de so sanh `>= 2 approaches + 1 reference`

## Cau truc

- `build_dataset_manifest.py`: quet dataset va tao manifest
- `generate_split.py`: tao chia `dev/test`
- `run_benchmark.py`: cham prediction tren tap co GT
- `compare_runs.py`: so sanh nhieu run benchmark
- `generate_error_analysis.py`: tao tom tat loi theo sample va theo nhom
- `record_experiment_config.py`: log config/model/prompt/preprocessing/seed truoc moi run
- `generate_weekly_report.py`: tao report hang tuan
- `generate_final_report.py`: tao report cuoi ky
- `normalization.py`: chuan hoa text/menu/price
- `validators.py`: validate schema va prediction
- `metrics.py`: tinh toan matching va metric
- `guardrail.py`: calibrate confidence threshold
- `configs/`: file cau hinh mau
- `templates/`: template markdown mau
- `artifacts/`: output sinh ra khi chay

## Quy uoc input prediction

Moi anh trong tap eval co 1 file JSON prediction trung ten voi GT.

Vi du:

- GT: `fastAPI/dataset/labels/beautiful_photos/menu_01.json`
- Prediction: `fastAPI/report/predictions/method_a/beautiful_photos/menu_01.json`

Co the them metadata trong prediction:

```json
{
  "categories": [...],
  "_meta": {
    "confidence": 0.82,
    "latency_ms": 1450,
    "method": "traditional_ocr_llm",
    "model_version": "gpt-4o-mini",
    "prompt_version": "prompt_v1",
    "schema_version": "schema_v1",
    "preprocessing": {
      "deskew": true,
      "contrast": false,
      "split_long_menu": true
    },
    "seed": 42
  }
}
```

Neu khong co `_meta.confidence`, toolkit se tu suy ra confidence heuristic de calibrate guardrail.

## Cach dung nhanh

### 1. Tao manifest dataset

```bash
python fastAPI/report/build_dataset_manifest.py
```

### 2. Tao chia dev/test

```bash
python fastAPI/report/generate_split.py
```

### 3. Cham mot run

```bash
python fastAPI/report/run_benchmark.py ^
  --predictions fastAPI/report/predictions/method_a ^
  --run-name method_a
```

### 4. So sanh nhieu run

```bash
python fastAPI/report/compare_runs.py ^
  --runs fastAPI/report/artifacts/benchmark_method_a.json fastAPI/report/artifacts/benchmark_method_b.json fastAPI/report/artifacts/benchmark_reference.json
```

### 5. Tao weekly report

```bash
python fastAPI/report/generate_weekly_report.py ^
  --benchmark fastAPI/report/artifacts/benchmark_method_a.json ^
  --week W3 ^
  --method-name method_a
```

### 6. Tao error analysis

```bash
python fastAPI/report/generate_error_analysis.py ^
  --benchmark fastAPI/report/artifacts/benchmark_method_a.json
```

### 7. Tao final report

```bash
python fastAPI/report/generate_final_report.py ^
  --comparison fastAPI/report/artifacts/run_comparison.json
```

## Ghi chu

- Toolkit nay khong goi API OCR/VLM. No cham prediction da sinh san.
- Neu muon benchmark nhieu huong, chi can dat prediction vao cac folder khac nhau roi chay `run_benchmark.py` cho tung folder.
- Tat ca artifact mac dinh se duoc ghi vao `fastAPI/report/artifacts/`.
