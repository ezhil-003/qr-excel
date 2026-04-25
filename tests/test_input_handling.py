import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from qr_excel.cli import prompts

def test_ask_input_path_handles_invalid_and_empty(tmp_path: Path):
    valid_file = tmp_path / "test.xlsx"
    valid_file.touch()
    
    # 1. Empty input, 2. Non-existent file, 3. Wrong extension, 4. Valid file
    inputs = ["", "nonexistent.xlsx", "wrong.txt", str(valid_file)]
    
    with patch("qr_excel.cli.prompts.Prompt.ask", side_effect=inputs) as mock_ask, \
         patch("qr_excel.cli.prompts.console.print") as mock_print:
        
        res = prompts.ask_input_path()
        assert res == valid_file.resolve()
        assert mock_ask.call_count == 4

def test_ask_amount_column_name_mandatory():
    inputs = ["", "   ", "Amount"]
    with patch("qr_excel.cli.prompts.Prompt.ask", side_effect=inputs) as mock_ask, \
         patch("qr_excel.cli.prompts.console.print") as mock_print:
        
        res = prompts.ask_amount_column_name()
        assert res == "Amount"
        assert mock_ask.call_count == 3

def test_ask_static_vpa_validation():
    # 1. Empty, 2. Invalid format, 3. Valid
    inputs = ["", "invalid_vpa", "merchant@okaxis"]
    with patch("qr_excel.cli.prompts.Prompt.ask", side_effect=inputs) as mock_ask, \
         patch("qr_excel.cli.prompts.console.print") as mock_print:
        
        res = prompts.ask_static_vpa()
        assert res == "merchant@okaxis"
        assert mock_ask.call_count == 3

def test_ask_static_payee_name_mandatory():
    inputs = ["", "Payee"]
    with patch("qr_excel.cli.prompts.Prompt.ask", side_effect=inputs) as mock_ask:
        res = prompts.ask_static_payee_name()
        assert res == "Payee"
        assert mock_ask.call_count == 2
