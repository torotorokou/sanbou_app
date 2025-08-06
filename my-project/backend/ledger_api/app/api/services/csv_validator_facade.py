from backend_shared.config.config_loader import SyogunCsvConfigLoader
from backend_shared.src.csv_validator.csv_upload_validator_api import (
    CSVValidationResponder,
)


class CsvValidatorService:
    def __init__(self):
        self.config_loader = SyogunCsvConfigLoader()

    def validate(self, dfs, files):
        required_columns = {
            k: self.config_loader.get_expected_headers(k) for k in files.keys()
        }
        validator = CSVValidationResponder(required_columns)

        res = validator.validate_columns(dfs, files)
        if res:
            return self._api_error("column_validation_error", res)

        res = validator.validate_denpyou_date_exists(dfs, files)
        if res:
            return self._api_error("date_missing", res)

        res = validator.validate_denpyou_date_consistency(dfs)
        if res:
            return self._api_error("date_inconsistent", res)

        return None

    def _api_error(self, code, res):
        return {
            "status_code": 422,
            "status_str": "error",
            "code": code,
            "detail": res.get("detail"),
            "result": res.get("result"),
            "hint": res.get("hint"),
        }
