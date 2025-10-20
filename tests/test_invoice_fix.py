"""
Test invoice functionality to ensure preview and generation work correctly
"""

import pytest
from unittest.mock import Mock, patch
import json
from pathlib import Path

# Test the invoice manager directly
def test_invoice_manager_data_structure():
    """Test that invoice manager returns expected data structure"""
    from src.business.invoice_manager import InvoiceManager
    from src.business.task_manager import TaskManager
    
    # Create a mock data directory
    data_dir = Path("/tmp/test_invoice")
    data_dir.mkdir(exist_ok=True)
    
    # Create a mock task manager with sample data
    task_manager = Mock(spec=TaskManager)
    task_manager.load_tasks.return_value = {
        "tasks": {
            "task1": {
                "name": "Development Task",
                "total_hours": 8.0,
                "exported": False,
                "parent_heading": "Development"
            },
            "task2": {
                "name": "Testing Task", 
                "total_hours": 4.0,
                "exported": False,
                "parent_heading": "Testing"
            }
        }
    }
    
    # Create invoice manager
    invoice_manager = InvoiceManager(data_dir, task_manager)
    
    # Mock rate manager
    with patch.object(invoice_manager.rate_manager, 'load_rates') as mock_rates, \
         patch.object(invoice_manager.rate_manager, 'calculate_hourly_rate') as mock_hourly_rate, \
         patch.object(invoice_manager.currency_manager, 'get_current_currency') as mock_currency, \
         patch.object(invoice_manager.currency_manager, 'format_currency') as mock_format:
        
        mock_rates.return_value = {"Development": 400, "Testing": 300}
        mock_hourly_rate.side_effect = lambda day_rate: day_rate / 8  # 8 hours per day
        mock_currency.return_value = {"symbol": "$", "code": "USD"}
        mock_format.side_effect = lambda amount, currency: f"${amount:.2f}"
        
        # Generate invoice
        result = invoice_manager.generate_invoice(include_exported=False)
        
        # Verify structure matches what the backend expects
        assert "items" in result
        assert len(result["items"]) == 2
        
        # Check first item structure
        item = result["items"][0]
        assert "task" in item
        assert "total_hours" in item
        assert "hour_rate" in item
        assert "amount" in item
        
        print("Invoice structure test passed!")
        return result


def test_backend_preview_endpoint_mock():
    """Mock test of the preview endpoint logic"""
    
    # Sample data that matches the invoice manager output
    mock_invoice_data = {
        "date": "2025-10-20",
        "currency": {"symbol": "$", "code": "USD"},
        "items": [
            {
                "task": "Development",
                "total_hours": 8.0,
                "hour_rate": "$50.00",
                "amount": "$400.00"
            },
            {
                "task": "Testing", 
                "total_hours": 4.0,
                "hour_rate": "$37.50",
                "amount": "$150.00"
            }
        ],
        "total": "$550.00"
    }
    
    # Simulate the preview generation logic
    preview_lines = []
    preview_lines.append("=== INVOICE PREVIEW ===")
    preview_lines.append("")
    
    if "items" in mock_invoice_data:
        preview_lines.append("ITEMS:")
        total_hours = 0
        for item in mock_invoice_data["items"]:
            hours = item.get('total_hours', 0)
            total_hours += hours
            preview_lines.append(
                f"• {item.get('task', 'N/A')}: {hours:.2f}h @ {item.get('hour_rate', 'N/A')}/hr = {item.get('amount', 'N/A')}"
            )

        preview_lines.append("")
        currency = mock_invoice_data.get('currency', {})
        currency_symbol = currency.get('symbol', '$') if isinstance(currency, dict) else '$'
        total_amount = mock_invoice_data.get('total', '0.00')
        preview_lines.append(f"TOTAL: {currency_symbol}{total_amount}")
        preview_lines.append(f"Total Hours: {total_hours:.2f}")
    
    preview_text = "\n".join(preview_lines)
    
    # Verify the preview looks correct
    assert "Development: 8.00h" in preview_text
    assert "Testing: 4.00h" in preview_text  
    assert "TOTAL: $550.00" in preview_text
    assert "Total Hours: 12.00" in preview_text
    
    print("Preview generation test passed!")
    print("Generated preview:")
    print(preview_text)
    
    return {"preview": preview_text, "status": "success"}


if __name__ == "__main__":
    print("Testing invoice functionality...")
    
    try:
        # Test invoice manager structure
        invoice_data = test_invoice_manager_data_structure()
        print(f"Invoice data structure: {json.dumps(invoice_data, indent=2)}")
        
        # Test preview generation
        preview_result = test_backend_preview_endpoint_mock()
        print(f"Preview result: {json.dumps(preview_result, indent=2)}")
        
        print("\n✅ All invoice tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()